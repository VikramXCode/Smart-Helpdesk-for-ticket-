"""
routes/tickets.py – Ticket CRUD and management endpoints.

Endpoints:
- POST   /tickets/          Create ticket (employee+)
- GET    /tickets/          List tickets (company-scoped, role-filtered)
- GET    /tickets/:id       Get single ticket detail
- PATCH  /tickets/:id       Update ticket
- POST   /tickets/:id/assign    Assign ticket
- POST   /tickets/:id/resolve   Resolve ticket
- GET    /tickets/:id/messages  Get message thread
- POST   /tickets/:id/messages  Add message to thread
- GET    /tickets/:id/similar-articles  Vector search for related articles
- GET    /tickets/:id/ai-suggestion     Get AI suggestion for ticket
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DB, require_it_staff
from app.models import AuditLog, Team, Ticket, TicketMessage, User
from app.schemas import (
    AISuggestionOut,
    AssignedTeamOut,
    AuthorOut,
    MessageCreate,
    MessageOut,
    SimilarArticleOut,
    TicketAssign,
    TicketCreate,
    TicketListItem,
    TicketListResponse,
    TicketOut,
    TicketUpdate,
)
from app.services import ai
from app.services.ai_client import analyze_ticket_with_ai
from app.services.notifications import (
    notify_ticket_agent_reply,
    notify_ticket_routed,
    notify_ticket_status_changed,
)
from app.services.vector import find_similar_articles
from app.utils.exceptions import ForbiddenError, NotFoundError
from app.config import settings

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = logging.getLogger(__name__)
FALLBACK_CATEGORY = "Others"
FALLBACK_TEAM = "Others"


def _is_self_service_issue(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(
        keyword in text
        for keyword in [
            "password reset",
            "reset password",
            "forgot password",
            "vpn reconnect",
            "vpn not connecting",
            "locked account",
            "mfa reset",
        ]
    )


def _relative_time(dt: Optional[datetime]) -> str:
    """Convert datetime to human-readable relative time string."""
    if not dt:
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    if delta.total_seconds() < 60:
        return "Just now"
    if delta.total_seconds() < 3600:
        mins = int(delta.total_seconds() / 60)
        return f"{mins}m ago"
    if delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}h ago"
    if delta.days == 1:
        return "Yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"
    if delta.days < 30:
        weeks = delta.days // 7
        return f"{weeks}w ago"
    return dt.strftime("%b %d, %Y")


def _format_message_time(dt: datetime) -> str:
    """Format timestamp for message thread display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if dt.date() == now.date():
        return "Today, " + dt.strftime("%I:%M %p")
    if dt.date() == (now - timedelta(days=1)).date():
        return "Yesterday, " + dt.strftime("%I:%M %p")
    return dt.strftime("%b %d, %I:%M %p")


async def _pick_assignee_for_team(
    db: AsyncSession,
    company_id: uuid.UUID,
    team_name: Optional[str],
) -> Optional[User]:
    """Pick the least-loaded IT staff member from the routed team."""
    if not team_name:
        return None

    team_result = await db.execute(
        select(Team).where(Team.company_id == company_id, Team.name == team_name)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        return None

    agents_result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.role == "it_staff",
            User.team_id == team.id,
        )
    )
    agents = agents_result.scalars().all()
    if not agents:
        return None

    best_agent: Optional[User] = None
    best_load: Optional[int] = None
    for agent in agents:
        load_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.assigned_to == agent.id,
                Ticket.status.notin_(["resolved", "closed", "auto_resolved"]),
            )
        )
        load = load_result.scalar() or 0
        if best_load is None or load < best_load:
            best_load = load
            best_agent = agent

    return best_agent


async def _get_ticket_or_404(db: AsyncSession, ticket_id: uuid.UUID) -> Ticket:
    """Fetch ticket with messages and relationships, raise 404 if not found."""
    result = await db.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.creator),
            selectinload(Ticket.assignee_user),
            selectinload(Ticket.messages).selectinload(TicketMessage.author),
        )
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket")
    return ticket


def _build_ticket_list_item(ticket: Ticket, creator: Optional[User] = None, assignee: Optional[User] = None) -> TicketListItem:
    """Build a TicketListItem from a Ticket ORM object."""
    has_ai = bool(ticket.ai_response or ticket.ai_suggestion)
    creator_obj = creator or getattr(ticket, 'creator', None)
    assignee_obj = assignee or getattr(ticket, 'assignee_user', None)

    return TicketListItem(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description[:200] + ("..." if len(ticket.description) > 200 else ""),
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        source=ticket.source,
        department=ticket.department,
        assigned_team=ticket.assigned_team,
        assigned_to=ticket.assigned_to,
        assignee_name=assignee_obj.full_name if assignee_obj else None,
        created_by=ticket.created_by,
        creator_name=creator_obj.full_name if creator_obj else None,
        has_ai_insight=has_ai,
        ai_confidence=ticket.ai_confidence,
        ai_predicted_category=ticket.ai_predicted_category,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        reported_at=_relative_time(ticket.created_at),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /tickets – Create
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=TicketListItem, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, current_user: CurrentUser, db: DB):
    """Create a new ticket with AI analysis and auto-resolution where applicable."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Super admins cannot create tickets directly")

    # Generate ticket number (e.g., INC-00042)
    count_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.company_id == current_user.company_id)
    )
    count = count_result.scalar() or 0
    ticket_number = f"INC-{count + 1:05d}"

    # Call AI service for analysis
    ai_analysis = None
    initial_status = "new"  # Default status
    ai_response_text = None
    ai_conf = None
    ai_cat = None
    ai_priority = None
    ai_assigned_team = None
    is_duplicate = False

    is_self_service = _is_self_service_issue(payload.title, payload.description)

    # Build tenant-scoped category/team constraints from team names only
    team_result = await db.execute(
        select(Team).where(Team.company_id == current_user.company_id)
    )
    teams = team_result.scalars().all()
    category_team_map = {
        team.name.strip(): team.name.strip()
        for team in teams
        if team.name and team.name.strip()
    }
    if not category_team_map:
        category_team_map[FALLBACK_CATEGORY] = FALLBACK_TEAM
    allowed_categories = list(category_team_map.keys())

    try:
        # Analyzeticket with AI
        ai_analysis = await analyze_ticket_with_ai(
            subject=payload.title,
            description=payload.description,
            company_id=str(current_user.company_id),
            allowed_categories=allowed_categories,
            category_team_map=category_team_map,
        )

        if ai_analysis and ai_analysis.get("success"):
            ai_response_text = ai_analysis.get("ai_response")
            ai_conf = ai_analysis.get("confidence")
            ai_cat = ai_analysis.get("category")
            ai_priority = ai_analysis.get("priority")
            ai_assigned_team = ai_analysis.get("assigned_team")
            is_duplicate = ai_analysis.get("is_duplicate", False)

            mapped_ai_cat = ai.map_to_allowed_category(ai_cat, allowed_categories)
            if mapped_ai_cat:
                ai_cat = mapped_ai_cat
            else:
                ai_cat = await ai.classify_ticket_to_allowed_category(
                    payload.title,
                    payload.description,
                    allowed_categories,
                )

            # Apply strict company mapping guard before persisting
            if ai_cat not in category_team_map:
                ai_cat = FALLBACK_CATEGORY
                ai_assigned_team = category_team_map.get(FALLBACK_CATEGORY, FALLBACK_TEAM)
            elif not ai_assigned_team:
                ai_assigned_team = category_team_map.get(ai_cat)

            # Auto-resolve if AI determines it should be resolved
            if ai_analysis.get("should_resolve", False):
                initial_status = "resolved"
    except Exception as e:
        # AI service unavailable - continue without AIanalysis
        print(f"AI analysis failed: {e}")
        ai_cat = await ai.classify_ticket_to_allowed_category(
            payload.title,
            payload.description,
            allowed_categories,
        )
        if not ai_cat:
            ai_cat = FALLBACK_CATEGORY
        ai_assigned_team = category_team_map.get(ai_cat, category_team_map.get(FALLBACK_CATEGORY, FALLBACK_TEAM))

    if is_self_service:
        if not ai_response_text:
            ai_response_text = (
                "I can help with this immediately. Please try: (1) sign out of all sessions, "
                "(2) reset credentials using the company self-service page, and "
                "(3) sign in again after 2-3 minutes. "
                "If this does not work, reply to this ticket and IT will assist."
            )
        if not ai_cat:
            ai_cat = "Software"
        initial_status = "auto_resolved"
        ai_assigned_team = None

    # Create ticket with AI data
    final_priority = ai_priority or payload.priority
    final_department = payload.department or ai_assigned_team
    auto_assignee = await _pick_assignee_for_team(db, current_user.company_id, ai_assigned_team)
    assigned_to_id = auto_assignee.id if auto_assignee else None
    if initial_status == "auto_resolved":
        assigned_to_id = None
    if assigned_to_id and initial_status == "new":
        initial_status = "assigned"

    ticket = Ticket(
        company_id=current_user.company_id,
        ticket_number=ticket_number,
        title=payload.title,
        description=payload.description,
        priority=final_priority,
        source=payload.source,
        department=final_department,
        created_by=current_user.id,
        status=initial_status,
        category=ai_cat,
        assigned_team=None if initial_status == "auto_resolved" else ai_assigned_team,
        assigned_to=assigned_to_id,
        # AI fields
        ai_response=ai_response_text,
        ai_confidence=ai_conf,
        ai_predicted_category=ai_cat,
        ai_suggested_priority=ai_priority,
        is_ai_duplicate=is_duplicate,
        resolved_at=datetime.now(timezone.utc) if initial_status == "resolved" else None,
    )
    db.add(ticket)
    await db.flush()

    # If AI provided a response, add it as the first message in the thread
    if ai_response_text:
        ai_message = TicketMessage(
            ticket_id=ticket.id,
            author_id=None,  # System/AI message
            content=ai_response_text,
            is_internal=False,
        )
        db.add(ai_message)

    # Audit
    audit_details = {
        "title": payload.title,
        "priority": payload.priority,
        "ai_analyzed": bool(ai_analysis),
        "auto_resolved": initial_status == "resolved"
    }
    db.add(AuditLog(
        company_id=current_user.company_id,
        user_id=current_user.id,
        action="ticket_created",
        details=audit_details,
    ))

    await db.commit()
    await db.refresh(ticket)

    if ticket.assigned_team:
        await notify_ticket_routed(
            ticket_number=ticket.ticket_number or str(ticket.id),
            ticket_title=ticket.title,
            reporter_email=current_user.email,
            team_name=ticket.assigned_team,
            assignee_name=auto_assignee.full_name if auto_assignee else None,
            frontend_url=settings.FRONTEND_URL,
        )

    return _build_ticket_list_item(ticket, creator=current_user, assignee=auto_assignee)


# ─────────────────────────────────────────────────────────────────────────────
# GET /tickets – List
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    current_user: CurrentUser,
    db: DB,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    assigned_team: Optional[str] = Query(None),
    assigned_to_me: bool = Query(False),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
):
    """List tickets scoped by company and role."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Use super-admin endpoints")

    query = (
        select(Ticket)
        .options(selectinload(Ticket.creator), selectinload(Ticket.assignee_user))
        .where(Ticket.company_id == current_user.company_id)
    )

    # Role-based filtering
    if current_user.role == "employee":
        query = query.where(Ticket.created_by == current_user.id)
    # it_staff, company_admin, super_admin see all company tickets (full queue)

    # Filters
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)
    if assigned_team:
        query = query.where(Ticket.assigned_team == assigned_team)
    if assigned_to_me:
        query = query.where(Ticket.assigned_to == current_user.id)
    if search:
        query = query.where(
            Ticket.title.ilike(f"%{search}%") | Ticket.description.ilike(f"%{search}%")
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_col = getattr(Ticket, sort, Ticket.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Paginate
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    tickets = result.scalars().all()

    return TicketListResponse(
        tickets=[_build_ticket_list_item(t) for t in tickets],
        total=total,
        page=page,
        limit=limit,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /tickets/:id – Single ticket detail
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Get full ticket details including messages and AI suggestion."""
    ticket = await _get_ticket_or_404(db, ticket_id)

    # Authorization: owner, IT staff, or admin
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        raise ForbiddenError("You can only view your own tickets")
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    # Build reporter
    reporter = None
    if ticket.creator:
        reporter = AuthorOut(
            id=ticket.creator.id,
            name=ticket.creator.full_name,
            avatar_url=ticket.creator.avatar_url,
            type="user",
            department=ticket.creator.department,
        )

    # Build assignee
    assignee = None
    if ticket.assignee_user:
        assignee = AuthorOut(
            id=ticket.assignee_user.id,
            name=ticket.assignee_user.full_name,
            avatar_url=ticket.assignee_user.avatar_url,
            type="agent",
            badge="Agent",
            status=ticket.assignee_user.status,
        )

    # Build messages
    messages_out = []
    for msg in ticket.messages:
        if msg.author_type == "ai":
            author = AuthorOut(name="HelpDesk AI", type="ai", badge="Automated")
        elif msg.author and msg.author.role in ("it_staff", "company_admin"):
            author = AuthorOut(
                id=msg.author.id,
                name=msg.author.full_name,
                avatar_url=msg.author.avatar_url,
                type="agent",
                badge="Agent",
            )
        else:
            author = AuthorOut(
                id=msg.author.id if msg.author else None,
                name=msg.author.full_name if msg.author else "User",
                avatar_url=msg.author.avatar_url if msg.author else None,
                type="user",
            )
        messages_out.append(
            MessageOut(
                id=msg.id,
                author=author,
                content=msg.content,
                is_internal=msg.is_internal,
                created_at=msg.created_at,
                timestamp=_format_message_time(msg.created_at),
            )
        )

    # AI suggestion
    ai_suggestion = None
    if ticket.ai_suggestion:
        # Parse confidence if embedded
        confidence = 75
        text = ticket.ai_suggestion
        if "(Confidence:" in text:
            parts = text.rsplit("(Confidence:", 1)
            text = parts[0].strip()
            try:
                confidence = int("".join(c for c in parts[1] if c.isdigit())[:3])
            except (ValueError, IndexError):
                pass
        ai_suggestion = AISuggestionOut(text=text, confidence=confidence)

    # Assigned team detail
    assigned_team_detail = None
    if ticket.assigned_team:
        assigned_team_detail = AssignedTeamOut(name=ticket.assigned_team)

    # Similar articles via vector search
    similar_articles = []
    if ticket.embedding is not None:
        try:
            similar = await find_similar_articles(db, ticket.company_id, ticket.embedding, limit=3)
            for article, sim in similar:
                similar_articles.append(
                    SimilarArticleOut(
                        id=article.id,
                        title=article.title,
                        tag=article.category or "",
                        summary=article.content[:150] + "..." if len(article.content) > 150 else article.content,
                        similarity=round(sim, 3),
                    )
                )
        except Exception as exc:
            logger.warning("Similar article lookup failed for ticket %s: %s", ticket.id, exc)

    return TicketOut(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        source=ticket.source,
        department=ticket.department,
        due_date=ticket.due_date,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        reported_at=_relative_time(ticket.created_at),
        reporter=reporter,
        assignee=assignee,
        assigned_team=ticket.assigned_team,
        assigned_team_detail=assigned_team_detail,
        ai_suggestion=ai_suggestion,
        messages=messages_out,
        similar_articles=similar_articles,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /tickets/:id – Update
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{ticket_id}", response_model=TicketListItem)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    current_user: CurrentUser,
    db: DB,
):
    """Update ticket fields. IT staff and above only."""
    if current_user.role == "employee":
        raise ForbiddenError("Employees cannot update tickets directly")

    ticket = await _get_ticket_or_404(db, ticket_id)
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    old_status = ticket.status

    # Apply updates
    if payload.status is not None:
        ticket.status = payload.status
        if payload.status in ("resolved", "auto_resolved") and not ticket.resolved_at:
            ticket.resolved_at = datetime.now(timezone.utc)
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.category is not None:
        ticket.category = payload.category
    if payload.assigned_team is not None:
        ticket.assigned_team = payload.assigned_team
    if payload.assigned_to is not None:
        ticket.assigned_to = payload.assigned_to
    if payload.due_date is not None:
        ticket.due_date = payload.due_date

    db.add(AuditLog(
        company_id=ticket.company_id,
        user_id=current_user.id,
        action="ticket_updated",
        details={"ticket_id": str(ticket_id), "changes": payload.model_dump(exclude_none=True)},
    ))

    await db.commit()
    await db.refresh(ticket)

    if ticket.status != old_status:
        reporter_result = await db.execute(select(User).where(User.id == ticket.created_by))
        reporter_user = reporter_result.scalar_one_or_none()
        await notify_ticket_status_changed(
            ticket_number=ticket.ticket_number or str(ticket.id),
            ticket_title=ticket.title,
            reporter_email=reporter_user.email if reporter_user else None,
            old_status=old_status,
            new_status=ticket.status,
            actor_name=current_user.full_name,
            frontend_url=settings.FRONTEND_URL,
        )

    return _build_ticket_list_item(ticket)


# ─────────────────────────────────────────────────────────────────────────────
# POST /tickets/:id/assign
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{ticket_id}/assign", response_model=TicketListItem)
async def assign_ticket(
    ticket_id: uuid.UUID,
    payload: TicketAssign,
    current_user: CurrentUser,
    db: DB,
    _: User = require_it_staff(),
):
    """Assign ticket to a team and/or user."""
    ticket = await _get_ticket_or_404(db, ticket_id)
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    if payload.assigned_team:
        ticket.assigned_team = payload.assigned_team
    if payload.assigned_to:
        ticket.assigned_to = payload.assigned_to
    if ticket.status == "new":
        ticket.status = "assigned"

    assignee_user: Optional[User] = None
    if ticket.assigned_to:
        assignee_result = await db.execute(select(User).where(User.id == ticket.assigned_to))
        assignee_user = assignee_result.scalar_one_or_none()

    await db.commit()
    await db.refresh(ticket)

    reporter_result = await db.execute(select(User).where(User.id == ticket.created_by))
    reporter_user = reporter_result.scalar_one_or_none()
    if reporter_user and reporter_user.email and ticket.assigned_team:
        await notify_ticket_routed(
            ticket_number=ticket.ticket_number or str(ticket.id),
            ticket_title=ticket.title,
            reporter_email=reporter_user.email,
            team_name=ticket.assigned_team,
            assignee_name=assignee_user.full_name if assignee_user else None,
            frontend_url=settings.FRONTEND_URL,
        )

    return _build_ticket_list_item(ticket, assignee=assignee_user)


# ─────────────────────────────────────────────────────────────────────────────
# POST /tickets/:id/resolve
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{ticket_id}/resolve", response_model=TicketListItem)
async def resolve_ticket(ticket_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Mark a ticket as resolved."""
    ticket = await _get_ticket_or_404(db, ticket_id)

    if current_user.role == "employee" and ticket.created_by != current_user.id:
        raise ForbiddenError()
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    old_status = ticket.status
    ticket.status = "resolved"
    ticket.resolved_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        company_id=ticket.company_id,
        user_id=current_user.id,
        action="ticket_resolved",
        details={"ticket_id": str(ticket_id)},
    ))

    await db.commit()
    await db.refresh(ticket)

    if old_status != "resolved":
        reporter_result = await db.execute(select(User).where(User.id == ticket.created_by))
        reporter_user = reporter_result.scalar_one_or_none()
        await notify_ticket_status_changed(
            ticket_number=ticket.ticket_number or str(ticket.id),
            ticket_title=ticket.title,
            reporter_email=reporter_user.email if reporter_user else None,
            old_status=old_status,
            new_status=ticket.status,
            actor_name=current_user.full_name,
            frontend_url=settings.FRONTEND_URL,
        )

    return _build_ticket_list_item(ticket)


# ─────────────────────────────────────────────────────────────────────────────
# GET/POST /tickets/:id/messages
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}/messages", response_model=List[MessageOut])
async def get_messages(ticket_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Get the conversation thread for a ticket."""
    ticket = await _get_ticket_or_404(db, ticket_id)
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    messages_out = []
    for msg in ticket.messages:
        author_type = msg.author_type
        if author_type == "ai":
            author = AuthorOut(name="HelpDesk AI", type="ai", badge="Automated")
        else:
            author = AuthorOut(
                id=msg.author.id if msg.author else None,
                name=msg.author.full_name if msg.author else "User",
                avatar_url=msg.author.avatar_url if msg.author else None,
                type=author_type,
                badge="Agent" if author_type == "agent" else None,
            )
        messages_out.append(MessageOut(
            id=msg.id,
            author=author,
            content=msg.content,
            is_internal=msg.is_internal,
            created_at=msg.created_at,
            timestamp=_format_message_time(msg.created_at),
        ))
    return messages_out


@router.post("/{ticket_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    ticket_id: uuid.UUID,
    payload: MessageCreate,
    current_user: CurrentUser,
    db: DB,
):
    """Add a message to the ticket conversation thread."""
    ticket = await _get_ticket_or_404(db, ticket_id)

    if current_user.role == "employee" and ticket.created_by != current_user.id:
        raise ForbiddenError()
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    # Determine author type
    author_type = "agent" if current_user.role in ("it_staff", "company_admin") else "user"

    msg = TicketMessage(
        ticket_id=ticket.id,
        author_id=current_user.id,
        author_type=author_type,
        content=payload.content,
        is_internal=payload.is_internal,
    )
    db.add(msg)

    status_before_reply = ticket.status

    # Move to in_progress when agent replies
    if author_type == "agent" and ticket.status in ("new", "assigned"):
        ticket.status = "in_progress"

    await db.commit()
    await db.refresh(msg)

    if author_type == "agent" and not payload.is_internal:
        reporter_result = await db.execute(select(User).where(User.id == ticket.created_by))
        reporter_user = reporter_result.scalar_one_or_none()
        await notify_ticket_agent_reply(
            ticket_number=ticket.ticket_number or str(ticket.id),
            ticket_title=ticket.title,
            reporter_email=reporter_user.email if reporter_user else None,
            agent_name=current_user.full_name,
            message_content=payload.content,
            frontend_url=settings.FRONTEND_URL,
        )

        if ticket.status != status_before_reply:
            await notify_ticket_status_changed(
                ticket_number=ticket.ticket_number or str(ticket.id),
                ticket_title=ticket.title,
                reporter_email=reporter_user.email if reporter_user else None,
                old_status=status_before_reply,
                new_status=ticket.status,
                actor_name=current_user.full_name,
                frontend_url=settings.FRONTEND_URL,
            )

    author = AuthorOut(
        id=current_user.id,
        name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        type=author_type,
        badge="Agent" if author_type == "agent" else None,
    )
    return MessageOut(
        id=msg.id,
        author=author,
        content=msg.content,
        is_internal=msg.is_internal,
        created_at=msg.created_at,
        timestamp=_format_message_time(msg.created_at),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /tickets/:id/similar-articles
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}/similar-articles", response_model=List[SimilarArticleOut])
async def get_similar_articles(ticket_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Find knowledge articles similar to this ticket (vector search)."""
    ticket = await _get_ticket_or_404(db, ticket_id)
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    if not ticket.embedding:
        return []

    similar = await find_similar_articles(db, ticket.company_id, ticket.embedding, limit=5)
    return [
        SimilarArticleOut(
            id=article.id,
            title=article.title,
            tag=article.category or "",
            summary=article.content[:150] + "..." if len(article.content) > 150 else article.content,
            similarity=round(sim, 3),
        )
        for article, sim in similar
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GET /tickets/:id/ai-suggestion
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}/ai-suggestion", response_model=AISuggestionOut)
async def get_ai_suggestion(ticket_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Get or generate an AI suggestion for the ticket."""
    ticket = await _get_ticket_or_404(db, ticket_id)
    if current_user.company_id and ticket.company_id != current_user.company_id:
        raise ForbiddenError()

    if ticket.ai_suggestion:
        confidence = 75
        text = ticket.ai_suggestion
        if "(Confidence:" in text:
            parts = text.rsplit("(Confidence:", 1)
            text = parts[0].strip()
            try:
                confidence = int("".join(c for c in parts[1] if c.isdigit())[:3])
            except (ValueError, IndexError):
                pass
        return AISuggestionOut(text=text, confidence=confidence)

    # Generate on the fly
    suggestion_text, confidence = await ai.generate_ticket_suggestion(
        ticket.title, ticket.description, ticket.category
    )
    ticket.ai_suggestion = f"{suggestion_text} (Confidence: {confidence}%)"
    await db.commit()

    return AISuggestionOut(text=suggestion_text, confidence=confidence)
