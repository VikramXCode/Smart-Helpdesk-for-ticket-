"""
routes/admin.py – Company admin management endpoints.

Requires company_admin or super_admin role for all routes.

Endpoints:
- GET    /admin/agents           List IT staff agents
- POST   /admin/agents           Create new agent (IT staff user)
- PATCH  /admin/agents/:id       Update agent profile
- DELETE /admin/agents/:id       Deactivate/delete agent

- GET    /admin/teams            List teams
- POST   /admin/teams            Create team
- PATCH  /admin/teams/:id        Update team
- DELETE /admin/teams/:id        Delete team

- GET    /admin/mappings         List category→team mappings
- POST   /admin/mappings         Bulk save mappings

- GET    /admin/notifications    List notification configs
- PUT    /admin/notifications    Update a notification config
"""
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from passlib.context import CryptContext
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB, require_company_admin
from app.models import CompanyTeamMapping, NotificationsConfig, Team, Ticket, User
from app.schemas import (
    AgentCreate,
    AgentListResponse,
    AgentOut,
    AgentUpdate,
    MappingBulkSave,
    MappingOut,
    NotificationsConfigOut,
    NotificationsConfigUpdate,
    TeamCreate,
    TeamOut,
    TeamUpdate,
)
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[require_company_admin()])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _build_agent_out(user: User, db) -> AgentOut:
    """Build AgentOut with live assigned_tickets count."""
    r = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.assigned_to == user.id,
            Ticket.status.notin_(["resolved", "closed", "auto_resolved"]),
        )
    )
    assigned = r.scalar() or 0

    team_name = None
    if user.team_id:
        r_team = await db.execute(select(Team).where(Team.id == user.team_id))
        team = r_team.scalar_one_or_none()
        team_name = team.name if team else None

    return AgentOut(
        id=user.id,
        name=user.full_name,
        email=user.email,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status or "offline",
        assigned_tickets=assigned,
        performance=85,  # placeholder; real metric would require more data
        team_id=user.team_id,
        team_name=team_name,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    current_user: CurrentUser,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List all IT staff / company admin agents for the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    query = select(User).where(
        User.company_id == cid,
        User.role.in_(["it_staff", "company_admin"]),
    )
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    agents = [await _build_agent_out(u, db) for u in users]
    return AgentListResponse(agents=agents, total=total, page=page, limit=limit)


@router.post("/agents", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, current_user: CurrentUser, db: DB):
    """Create a new IT staff agent under the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    # Check email uniqueness within company
    r = await db.execute(
        select(User).where(User.company_id == cid, User.email == payload.email)
    )
    if r.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered in this company")

    # Validate role
    if payload.role not in ("it_staff", "company_admin"):
        raise HTTPException(status_code=400, detail="Role must be it_staff or company_admin")

    user = User(
        company_id=cid,
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        team_id=payload.team_id,
        department=payload.department,
        status="offline",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _build_agent_out(user, db)


@router.patch("/agents/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: uuid.UUID, payload: AgentUpdate, current_user: CurrentUser, db: DB
):
    """Update an agent's profile fields."""
    r = await db.execute(select(User).where(User.id == agent_id))
    user = r.scalar_one_or_none()
    if not user:
        raise NotFoundError("Agent")
    if current_user.company_id and user.company_id != current_user.company_id:
        raise ForbiddenError()

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.team_id is not None:
        user.team_id = payload.team_id
    if payload.status is not None:
        user.status = payload.status
    if payload.department is not None:
        user.department = payload.department

    await db.commit()
    await db.refresh(user)
    return await _build_agent_out(user, db)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Remove an agent from the company."""
    r = await db.execute(select(User).where(User.id == agent_id))
    user = r.scalar_one_or_none()
    if not user:
        raise NotFoundError("Agent")
    if current_user.company_id and user.company_id != current_user.company_id:
        raise ForbiddenError()
    await db.delete(user)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Teams
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/teams", response_model=List[TeamOut])
async def list_teams(current_user: CurrentUser, db: DB):
    """List all teams for the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    r = await db.execute(select(Team).where(Team.company_id == cid).order_by(Team.name))
    teams = r.scalars().all()

    result = []
    for team in teams:
        r_count = await db.execute(
            select(func.count(User.id)).where(User.team_id == team.id)
        )
        member_count = r_count.scalar() or 0
        result.append(
            TeamOut(
                id=team.id,
                company_id=team.company_id,
                name=team.name,
                email=team.email,
                member_count=member_count,
                created_at=team.created_at,
            )
        )
    return result


@router.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(payload: TeamCreate, current_user: CurrentUser, db: DB):
    """Create a new team under the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    # Check name uniqueness
    r = await db.execute(
        select(Team).where(Team.company_id == cid, Team.name == payload.name)
    )
    if r.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Team name already exists")

    team = Team(company_id=cid, name=payload.name, email=str(payload.email) if payload.email else None)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return TeamOut(
        id=team.id,
        company_id=team.company_id,
        name=team.name,
        email=team.email,
        member_count=0,
        created_at=team.created_at,
    )


@router.patch("/teams/{team_id}", response_model=TeamOut)
async def update_team(team_id: uuid.UUID, payload: TeamUpdate, current_user: CurrentUser, db: DB):
    """Update a team's name or email."""
    r = await db.execute(select(Team).where(Team.id == team_id))
    team = r.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team")
    if current_user.company_id and team.company_id != current_user.company_id:
        raise ForbiddenError()

    if payload.name is not None:
        team.name = payload.name
    if payload.email is not None:
        team.email = str(payload.email)

    await db.commit()
    await db.refresh(team)

    r_count = await db.execute(select(func.count(User.id)).where(User.team_id == team.id))
    member_count = r_count.scalar() or 0
    return TeamOut(
        id=team.id,
        company_id=team.company_id,
        name=team.name,
        email=team.email,
        member_count=member_count,
        created_at=team.created_at,
    )


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Delete a team."""
    r = await db.execute(select(Team).where(Team.id == team_id))
    team = r.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team")
    if current_user.company_id and team.company_id != current_user.company_id:
        raise ForbiddenError()
    await db.delete(team)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Category → Team Mappings
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/mappings", response_model=List[MappingOut])
async def get_mappings(current_user: CurrentUser, db: DB):
    """List category→team routing mappings for this company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    r = await db.execute(
        select(CompanyTeamMapping)
        .where(CompanyTeamMapping.company_id == cid)
        .order_by(CompanyTeamMapping.category)
    )
    return list(r.scalars().all())


@router.post("/mappings", response_model=List[MappingOut])
async def save_mappings(payload: MappingBulkSave, current_user: CurrentUser, db: DB):
    """Bulk replace all category→team mappings for this company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    # Delete existing mappings for this company
    r = await db.execute(
        select(CompanyTeamMapping).where(CompanyTeamMapping.company_id == cid)
    )
    existing = r.scalars().all()
    for mapping in existing:
        await db.delete(mapping)

    # Insert new mappings
    new_mappings = []
    for item in payload.mappings:
        m = CompanyTeamMapping(
            company_id=cid,
            category=item.category,
            team_name=item.team_name,
        )
        db.add(m)
        new_mappings.append(m)

    await db.commit()
    for m in new_mappings:
        await db.refresh(m)

    return new_mappings


# ─────────────────────────────────────────────────────────────────────────────
# Notifications Config
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationsConfigOut])
async def get_notifications(current_user: CurrentUser, db: DB):
    """Get notification configuration for each event type."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    r = await db.execute(
        select(NotificationsConfig).where(NotificationsConfig.company_id == cid)
    )
    configs = r.scalars().all()

    # Auto-create default configs if none exist yet
    if not configs:
        events = ["ticket_created", "ticket_assigned", "ticket_resolved", "ticket_escalated"]
        configs = []
        for event in events:
            cfg = NotificationsConfig(
                company_id=cid,
                event_type=event,
                email_enabled=True,
                sms_enabled=False,
                email_recipients=[],
                sms_recipients=[],
            )
            db.add(cfg)
            configs.append(cfg)
        await db.commit()
        for cfg in configs:
            await db.refresh(cfg)

    return configs


@router.put("/notifications", response_model=NotificationsConfigOut)
async def update_notification(payload: NotificationsConfigUpdate, current_user: CurrentUser, db: DB):
    """Create or update a notification config for a specific event type."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    r = await db.execute(
        select(NotificationsConfig).where(
            NotificationsConfig.company_id == cid,
            NotificationsConfig.event_type == payload.event_type,
        )
    )
    cfg = r.scalar_one_or_none()

    if cfg:
        cfg.email_enabled = payload.email_enabled
        cfg.sms_enabled = payload.sms_enabled
        cfg.email_recipients = payload.email_recipients
        cfg.sms_recipients = payload.sms_recipients
    else:
        cfg = NotificationsConfig(
            company_id=cid,
            event_type=payload.event_type,
            email_enabled=payload.email_enabled,
            sms_enabled=payload.sms_enabled,
            email_recipients=payload.email_recipients,
            sms_recipients=payload.sms_recipients,
        )
        db.add(cfg)

    await db.commit()
    await db.refresh(cfg)
    return cfg
