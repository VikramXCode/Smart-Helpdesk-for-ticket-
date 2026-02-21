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
import re
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
    EmployeeBulkCreateRequest,
    EmployeeBulkCreateResponse,
    EmployeeCreateRequest,
    EmployeeCreateResponse,
    MappingBulkSave,
    MappingOut,
    NotificationsConfigOut,
    NotificationsConfigUpdate,
    TeamCreate,
    TeamOut,
    TeamUpdate,
    TeamAssignAgentRequest,
    TeamRemoveAgentRequest,
)
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[require_company_admin()])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_AGENT_PASSWORD = "12345678"
DEFAULT_EMPLOYEE_PASSWORD = "12345678"
FALLBACK_CATEGORY = "Others"
FALLBACK_TEAM = "Others"
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


async def _sync_team_name_mappings(db: DB, company_id):
    """Persist mappings where category == team_name for all company teams."""
    existing_result = await db.execute(
        select(CompanyTeamMapping).where(CompanyTeamMapping.company_id == company_id)
    )
    for mapping in existing_result.scalars().all():
        await db.delete(mapping)

    teams_result = await db.execute(
        select(Team).where(Team.company_id == company_id).order_by(Team.name)
    )
    teams = teams_result.scalars().all()

    for team in teams:
        if not team.name:
            continue
        normalized_name = team.name.strip()
        if not normalized_name:
            continue
        db.add(
            CompanyTeamMapping(
                company_id=company_id,
                category=normalized_name,
                team_name=normalized_name,
            )
        )


def _name_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    normalized = re.sub(r"[._-]+", " ", local).strip()
    if not normalized:
        return "Employee"
    return " ".join(part.capitalize() for part in normalized.split())


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
    """List all IT staff agents for the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    query = select(User).where(
        User.company_id == cid,
        User.role == "it_staff",
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

    # Agents are IT staff only
    if payload.role and payload.role != "it_staff":
        raise HTTPException(status_code=400, detail="Agents must have role it_staff")

    user = User(
        company_id=cid,
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password or DEFAULT_AGENT_PASSWORD),
        full_name=payload.full_name,
        role="it_staff",
        team_id=payload.team_id,
        department=payload.department,
        status="offline",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _build_agent_out(user, db)


@router.post("/employees", response_model=EmployeeCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(payload: EmployeeCreateRequest, current_user: CurrentUser, db: DB):
    """Create one employee user under current company with default initial password."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    email = payload.email.strip().lower()

    existing = await db.execute(
        select(User).where(User.company_id == cid, User.email == email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists in this company")

    user = User(
        company_id=cid,
        email=email,
        hashed_password=pwd_context.hash(DEFAULT_EMPLOYEE_PASSWORD),
        full_name=(payload.full_name.strip() if payload.full_name else _name_from_email(email)),
        role="employee",
        status="offline",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return EmployeeCreateResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


@router.post("/employees/bulk-create", response_model=EmployeeBulkCreateResponse)
async def bulk_create_employees(payload: EmployeeBulkCreateRequest, current_user: CurrentUser, db: DB):
    """Bulk-create employee users from email list for the current company."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    if not payload.emails:
        raise HTTPException(status_code=400, detail="No emails provided")

    normalized_emails: list[str] = []
    skipped: set[str] = set()
    seen: set[str] = set()

    for raw in payload.emails:
        email = (raw or "").strip().lower()
        if not email:
            continue
        if not EMAIL_REGEX.match(email):
            skipped.add(email)
            continue
        if email in seen:
            skipped.add(email)
            continue
        seen.add(email)
        normalized_emails.append(email)

    if not normalized_emails:
        return EmployeeBulkCreateResponse(created_count=0, created_emails=[], skipped_emails=sorted(skipped))

    existing_rows = await db.execute(
        select(User.email).where(
            User.company_id == cid,
            User.email.in_(normalized_emails),
        )
    )
    existing_emails = {row[0].strip().lower() for row in existing_rows.all() if row[0]}
    skipped.update(existing_emails)

    to_create = [email for email in normalized_emails if email not in existing_emails]
    created_emails: list[str] = []
    for email in to_create:
        user = User(
            company_id=cid,
            email=email,
            hashed_password=pwd_context.hash(DEFAULT_EMPLOYEE_PASSWORD),
            full_name=_name_from_email(email),
            role="employee",
            status="offline",
        )
        db.add(user)
        created_emails.append(email)

    await db.commit()

    return EmployeeBulkCreateResponse(
        created_count=len(created_emails),
        created_emails=created_emails,
        skipped_emails=sorted(skipped),
    )


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
    if payload.role is not None and payload.role != "it_staff":
        raise HTTPException(status_code=400, detail="Agents must have role it_staff")
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
                description=team.description,
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

    team = Team(
        company_id=cid,
        name=payload.name,
        description=payload.description,
        email=str(payload.email) if payload.email else None
    )
    db.add(team)
    await db.flush()
    await _sync_team_name_mappings(db, cid)
    await db.commit()
    await db.refresh(team)
    return TeamOut(
        id=team.id,
        company_id=team.company_id,
        name=team.name,
        description=team.description,
        email=team.email,
        member_count=0,
        created_at=team.created_at,
    )


@router.patch("/teams/{team_id}", response_model=TeamOut)
async def update_team(team_id: uuid.UUID, payload: TeamUpdate, current_user: CurrentUser, db: DB):
    """Update a team's name, description, or email."""
    r = await db.execute(select(Team).where(Team.id == team_id))
    team = r.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team")
    if current_user.company_id and team.company_id != current_user.company_id:
        raise ForbiddenError()

    if payload.name is not None:
        team.name = payload.name
    if payload.description is not None:
        team.description = payload.description
    if payload.email is not None:
        team.email = str(payload.email)

    await _sync_team_name_mappings(db, team.company_id)
    await db.commit()
    await db.refresh(team)

    r_count = await db.execute(select(func.count(User.id)).where(User.team_id == team.id))
    member_count = r_count.scalar() or 0
    return TeamOut(
        id=team.id,
        company_id=team.company_id,
        name=team.name,
        description=team.description,
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
    company_id = team.company_id
    await db.delete(team)
    await db.flush()
    await _sync_team_name_mappings(db, company_id)
    await db.commit()


@router.post("/teams/{team_id}/agents", response_model=AgentOut)
async def assign_agent_to_team(
    team_id: uuid.UUID,
    payload: TeamAssignAgentRequest,
    current_user: CurrentUser,
    db: DB
):
    """Assign an agent to a team."""
    # Verify team exists and belongs to current company
    r_team = await db.execute(select(Team).where(Team.id == team_id))
    team = r_team.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team")
    if current_user.company_id and team.company_id != current_user.company_id:
        raise ForbiddenError()

    # Verify agent exists and is in the same company
    r_agent = await db.execute(select(User).where(User.id == payload.agent_id))
    agent = r_agent.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent")
    if agent.role != "it_staff":
        raise HTTPException(status_code=400, detail="Only IT staff can be assigned to teams")
    if agent.company_id != team.company_id:
        raise HTTPException(status_code=400, detail="Agent must be from the same company")

    # Assign agent to team
    agent.team_id = team_id
    await db.commit()
    await db.refresh(agent)

    return await _build_agent_out(agent, db)


@router.delete("/teams/{team_id}/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_from_team(
    team_id: uuid.UUID,
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB
):
    """Remove an agent from a team."""
    # Verify team exists and belongs to current company
    r_team = await db.execute(select(Team).where(Team.id == team_id))
    team = r_team.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team")
    if current_user.company_id and team.company_id != current_user.company_id:
        raise ForbiddenError()

    # Verify agent exists and is in the team
    r_agent = await db.execute(select(User).where(User.id == agent_id))
    agent = r_agent.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent")
    if agent.team_id != team_id:
        raise HTTPException(status_code=400, detail="Agent is not in this team")

    # Remove agent from team
    agent.team_id = None
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Category → Team Mappings
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/mappings", response_model=List[MappingOut])
async def get_mappings(current_user: CurrentUser, db: DB):
    """List category→team routing mappings (category is always team name)."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    await _sync_team_name_mappings(db, cid)
    await db.commit()

    r = await db.execute(
        select(CompanyTeamMapping)
        .where(CompanyTeamMapping.company_id == cid)
        .order_by(CompanyTeamMapping.category)
    )
    return list(r.scalars().all())


@router.post("/mappings", response_model=List[MappingOut])
async def save_mappings(payload: MappingBulkSave, current_user: CurrentUser, db: DB):
    """Sync mappings from team names only (manual category mappings are ignored)."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Super admins must specify a company")

    await _sync_team_name_mappings(db, cid)
    await db.commit()

    synced = await db.execute(
        select(CompanyTeamMapping)
        .where(CompanyTeamMapping.company_id == cid)
        .order_by(CompanyTeamMapping.category)
    )
    return list(synced.scalars().all())


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
