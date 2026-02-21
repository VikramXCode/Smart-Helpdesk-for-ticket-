"""
routes/chat.py – AI chatbot endpoint.

Handles conversational AI for the floating helpdesk chatbot.
Can detect ticket creation intent and create tickets inline.
"""
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models import AuditLog, Team, Ticket, TicketMessage, User
from app.schemas import ChatRequest, ChatResponse, SimilarArticleOut, TicketCreate, TicketListItem
from app.services.ai import chat_with_ai, classify_ticket_to_allowed_category, generate_embedding, generate_ticket_suggestion
from app.services.vector import find_similar_articles

router = APIRouter(prefix="/chat", tags=["chat"])

# Keywords that suggest the user wants to create a ticket
TICKET_INTENT_KEYWORDS = [
    "create ticket", "submit ticket", "open ticket", "file ticket",
    "report issue", "report problem", "log issue", "raise ticket",
    "can't", "cannot", "not working", "broken", "error", "failed",
    "issue with", "problem with", "help with",
]
TICKET_EXPLICIT_KEYWORDS = [
    "create ticket", "submit ticket", "open ticket", "file ticket", "raise ticket", "report issue", "report problem"
]

PASSWORD_RESET_KEYWORDS = ["password", "forgot password", "reset password", "locked out", "cannot login", "can't login"]
VPN_KEYWORDS = ["vpn", "remote access", "connectivity", "cannot connect", "can't connect", "connection timed out"]


def _is_affirmative(message: str) -> bool:
    text = message.strip().lower()
    return text in {"yes", "y", "done", "resolved", "fixed", "worked", "it worked", "solved"}


def _is_negative(message: str) -> bool:
    text = message.strip().lower()
    return text in {"no", "n", "not working", "didn't work", "did not work", "failed", "still not working", "still failing"}


def _detect_self_service_topic(message: str) -> str | None:
    lowered = message.lower()
    if any(keyword in lowered for keyword in PASSWORD_RESET_KEYWORDS):
        return "password_reset"
    if any(keyword in lowered for keyword in VPN_KEYWORDS):
        return "vpn_access"
    return None


def _extract_last_playbook_topic(history: list[dict]) -> str | None:
    for item in reversed(history or []):
        content = (item.get("content") or "").lower()
        if "password reset self-service" in content:
            return "password_reset"
        if "vpn access self-service" in content:
            return "vpn_access"
    return None


def _count_playbook_attempts(history: list[dict], topic: str) -> int:
    marker = "password reset self-service" if topic == "password_reset" else "vpn access self-service"
    return sum(1 for item in history or [] if marker in (item.get("content") or "").lower())


def _playbook_response(topic: str, attempt: int, user_first_name: str) -> str:
    if topic == "password_reset":
        if attempt <= 1:
            return (
                f"Password reset self-service for {user_first_name}:\n"
                "1) Open your company SSO password reset page.\n"
                "2) Enter your work email and choose \"Forgot Password\".\n"
                "3) Complete MFA verification.\n"
                "4) Set a new strong password and sign in again.\n"
                "Did this solve your issue? (yes/no)"
            )
        return (
            f"Password reset self-service (retry) for {user_first_name}:\n"
            "1) Clear browser cache or use incognito.\n"
            "2) Ensure device time is correct (MFA can fail if clock drift exists).\n"
            "3) Retry reset and approve MFA prompt within 30 seconds.\n"
            "Did this solve your issue? (yes/no)"
        )

    if attempt <= 1:
        return (
            f"VPN access self-service for {user_first_name}:\n"
            "1) Verify internet is stable (try a speed test).\n"
            "2) Disconnect VPN and reconnect after 30 seconds.\n"
            "3) Re-authenticate with MFA and confirm company VPN profile.\n"
            "4) Restart VPN client if tunnel fails.\n"
            "Did this solve your issue? (yes/no)"
        )
    return (
        f"VPN access self-service (retry) for {user_first_name}:\n"
        "1) Switch network (mobile hotspot) to isolate local router issues.\n"
        "2) Flush DNS and restart system network adapter.\n"
        "3) Reinstall/repair VPN client profile and retry connection.\n"
        "Did this solve your issue? (yes/no)"
    )


async def _pick_assignee_for_team(db: DB, company_id: uuid.UUID, team_name: str | None) -> User | None:
    if not team_name:
        return None

    team_result = await db.execute(
        select(Team).where(Team.company_id == company_id, Team.name == team_name)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        return None

    staff_result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.role == "it_staff",
            User.team_id == team.id,
        )
    )
    staff = staff_result.scalars().all()
    if not staff:
        return None

    best_user = None
    best_load = None
    for candidate in staff:
        load_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.assigned_to == candidate.id,
                Ticket.status.notin_(["resolved", "closed", "auto_resolved"]),
            )
        )
        load = load_result.scalar() or 0
        if best_load is None or load < best_load:
            best_load = load
            best_user = candidate

    return best_user


async def _create_ticket_from_chat(
    db: DB,
    current_user: CurrentUser,
    title: str,
    description: str,
) -> TicketListItem | None:
    if not current_user.company_id:
        return None

    team_result = await db.execute(
        select(Team).where(Team.company_id == current_user.company_id)
    )
    teams = team_result.scalars().all()
    allowed_categories = [team.name.strip() for team in teams if team.name and team.name.strip()]
    if not allowed_categories:
        allowed_categories = ["Others"]

    selected_category = await classify_ticket_to_allowed_category(title, description, allowed_categories)
    if not selected_category:
        selected_category = allowed_categories[0]

    assignee = await _pick_assignee_for_team(db, current_user.company_id, selected_category)

    count_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.company_id == current_user.company_id)
    )
    count = count_result.scalar() or 0
    ticket_number = f"INC-{count + 1:05d}"

    suggestion_text, confidence = await generate_ticket_suggestion(title, description, selected_category)

    now = datetime.now(timezone.utc)
    ticket = Ticket(
        company_id=current_user.company_id,
        ticket_number=ticket_number,
        title=title,
        description=description,
        status="assigned" if assignee else "new",
        priority="medium",
        category=selected_category,
        source="chat",
        department=selected_category,
        assigned_team=selected_category,
        assigned_to=assignee.id if assignee else None,
        created_by=current_user.id,
        ai_suggestion=suggestion_text,
        ai_confidence=confidence,
        ai_predicted_category=selected_category,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    await db.flush()

    db.add(
        TicketMessage(
            ticket_id=ticket.id,
            author_id=current_user.id,
            author_type="user",
            content=description,
            is_internal=False,
        )
    )

    db.add(
        AuditLog(
            company_id=current_user.company_id,
            user_id=current_user.id,
            action="ticket_created_from_chat",
            details={
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.ticket_number,
                "category": selected_category,
            },
        )
    )
    await db.commit()

    return TicketListItem(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        source=ticket.source,
        department=ticket.department,
        assigned_team=ticket.assigned_team,
        assigned_to=ticket.assigned_to,
        assignee_name=assignee.full_name if assignee else None,
        created_by=ticket.created_by,
        creator_name=current_user.full_name,
        has_ai_insight=bool(ticket.ai_suggestion),
        ai_confidence=ticket.ai_confidence,
        ai_predicted_category=ticket.ai_predicted_category,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        reported_at="Just now",
    )


@router.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: CurrentUser, db: DB):
    """
    Process a chat message and return an AI response.

    Intent detection:
    - If message looks like a ticket creation request, creates the ticket
    - If message looks like a knowledge search, runs vector search
    - Otherwise, returns conversational AI response
    """
    message_lower = payload.message.lower().strip()
    user_first_name = (current_user.full_name or "User").split(" ")[0]
    history = payload.conversation_history or []

    prior_topic = _extract_last_playbook_topic(history)

    # If previous self-service flow asked yes/no, handle outcome first
    if prior_topic and _is_affirmative(message_lower):
        return ChatResponse(
            response=f"Great, {user_first_name}! Happy to help. I'll mark this as resolved in chat. If it happens again, I can create a ticket instantly.",
            intent="self_service_resolved",
            ticket_created=None,
            suggested_articles=[],
        )

    if prior_topic and _is_negative(message_lower):
        attempts = _count_playbook_attempts(history, prior_topic)
        if attempts >= 2:
            ticket_title = "Password reset issue" if prior_topic == "password_reset" else "VPN access issue"
            ticket_description = (
                f"User {current_user.full_name} reported unresolved issue via chatbot. "
                f"Topic: {prior_topic}. Latest input: {payload.message}"
            )
            created = await _create_ticket_from_chat(db, current_user, ticket_title, ticket_description)
            response = "I couldn't resolve it in self-service, so I created a ticket for IT to follow up."
            if created:
                response += f" Ticket {created.ticket_number} has been raised and routed."
            return ChatResponse(
                response=response,
                intent="ticket_creation",
                ticket_created=created,
                suggested_articles=[],
            )

        # Retry playbook step before escalation
        return ChatResponse(
            response=_playbook_response(prior_topic, attempts + 1, user_first_name),
            intent="self_service",
            ticket_created=None,
            suggested_articles=[],
        )

    # ── Detect intent ────────────────────────────────────────────────────────
    intent = "general"
    ticket_intent_score = sum(1 for kw in TICKET_INTENT_KEYWORDS if kw in message_lower)
    self_service_topic = _detect_self_service_topic(message_lower)

    if any(keyword in message_lower for keyword in TICKET_EXPLICIT_KEYWORDS) or ticket_intent_score >= 2:
        intent = "ticket_creation"
    elif any(kw in message_lower for kw in ["how to", "how do", "what is", "guide", "tutorial", "steps"]):
        intent = "knowledge_search"

    if self_service_topic:
        return ChatResponse(
            response=_playbook_response(self_service_topic, 1, user_first_name),
            intent="self_service",
            ticket_created=None,
            suggested_articles=[],
        )

    # ── Knowledge search ─────────────────────────────────────────────────────
    suggested_articles = []
    if current_user.company_id:
        embedding = await generate_embedding(payload.message)
        similar = await find_similar_articles(db, current_user.company_id, embedding, limit=3)
        suggested_articles = [
            SimilarArticleOut(
                id=article.id,
                title=article.title,
                tag=article.category or "",
                summary=article.content[:120] + "..." if len(article.content) > 120 else article.content,
                similarity=round(sim, 3),
            )
            for article, sim in similar
        ]

    if intent == "ticket_creation":
        created = await _create_ticket_from_chat(
            db,
            current_user,
            title=(payload.message[:120] if payload.message else "Chat-reported issue"),
            description=payload.message,
        )
        response = "I created a ticket from your chat message."
        if created:
            response += f" Ticket {created.ticket_number} is now in the queue."
            if created.assigned_team:
                response += f" Routed to {created.assigned_team} team"
                if created.assignee_name:
                    response += f" and assigned to {created.assignee_name}"
                response += "."
        return ChatResponse(
            response=response,
            intent=intent,
            ticket_created=created,
            suggested_articles=suggested_articles,
        )

    # ── Build context for AI ─────────────────────────────────────────────────
    context = None
    if suggested_articles:
        context = "Relevant knowledge base articles:\n" + "\n".join(
            f"- {a.title}: {a.summary}" for a in suggested_articles
        )
    user_context = (
        f"Authenticated employee context: name={current_user.full_name}, email={current_user.email}, role={current_user.role}. "
        "Do not ask the user for their name or email again."
    )
    if context:
        context = f"{context}\n\n{user_context}"
    else:
        context = user_context

    # ── AI response ──────────────────────────────────────────────────────────
    response_text = await chat_with_ai(
        message=payload.message,
        context=context,
        conversation_history=payload.conversation_history,
    )

    return ChatResponse(
        response=response_text,
        intent=intent,
        ticket_created=None,  # Frontend can use this to show ticket creation confirmation
        suggested_articles=suggested_articles,
    )
