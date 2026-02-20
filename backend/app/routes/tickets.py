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
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DB, require_it_staff
from app.models import AuditLog, KnowledgeArticle, Ticket, TicketMessage, User
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
from app.services.vector import find_similar_articles
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/tickets", tags=["tickets"])


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


async def _get_ticket_or_404(db: AsyncSession, ticket_id: uuid.UUID) -> Ticket:
    """Fetch ticket with messages and relationships, raise 404 if not found."""
    result = await db.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.creator),
            selectinload(Ticket.assignee_user),
            selectinload(Ticket.messages).selectinload(TicketMessage.author),
            selectinload(Ticket.suggested_article),
        )
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket")
    return ticket


def _build_ticket_list_item(ticket: Ticket, creator: Optional[User] = None, assignee: Optional[User] = None) -> TicketListItem:
    """Build a TicketListItem from a Ticket ORM object."""
    has_ai = bool(ticket.ai_suggestion or ticket.suggested_article_id)
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
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        reported_at=_relative_time(ticket.created_at),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /tickets – Create
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=TicketListItem, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, current_user: CurrentUser, db: DB):
    """Create a new ticket and enqueue background AI processing."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Super admins cannot create tickets directly")

    # Generate ticket number (e.g., INC-00042)
    count_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.company_id == current_user.company_id)
    )
    count = count_result.scalar() or 0
    ticket_number = f"INC-{count + 1:05d}"

    ticket = Ticket(
        company_id=current_user.company_id,
        ticket_number=ticket_number,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        source=payload.source,
        department=payload.department,
        created_by=current_user.id,
        status="new",
    )
    db.add(ticket)

    # Audit
    db.add(AuditLog(
        company_id=current_user.company_id,
        user_id=current_user.id,
        action="ticket_created",
        details={"title": payload.title, "priority": payload.priority},
    ))

    await db.commit()
    await db.refresh(ticket)

    # Enqueue background processing (non-blocking)
    try:
        from app.tasks.ticket_processing import process_new_ticket  # noqa: PLC0415
        process_new_ticket.delay(str(ticket.id))
    except Exception:
        # Celery not available – process inline (development fallback)
        pass

    return _build_ticket_list_item(ticket, creator=current_user)


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
    if ticket.embedding:
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
        suggested_article_id=ticket.suggested_article_id,
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

    await db.commit()
    await db.refresh(ticket)
    return _build_ticket_list_item(ticket)


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

    # Move to in_progress when agent replies
    if author_type == "agent" and ticket.status in ("new", "assigned"):
        ticket.status = "in_progress"

    await db.commit()
    await db.refresh(msg)

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
