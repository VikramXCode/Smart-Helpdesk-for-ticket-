import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models import Company, CompanyIssue, CompanyIssueMessage, User
from app.schemas import IssueCreate, IssueDetailOut, IssueMessageCreate, IssueMessageOut, IssueOut
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/issues", tags=["issues"])


async def _require_issue_role(user: User):
    if user.role not in ("company_admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only company admin and super admin can access issues")


async def _get_issue_or_404(db, issue_id: uuid.UUID) -> CompanyIssue:
    issue = (await db.execute(select(CompanyIssue).where(CompanyIssue.id == issue_id))).scalar_one_or_none()
    if not issue:
        raise NotFoundError("Issue")
    return issue


async def _build_issue_out(db, issue: CompanyIssue) -> IssueOut:
    company_name = (await db.execute(select(Company.name).where(Company.id == issue.company_id))).scalar_one_or_none()
    creator_name = (await db.execute(select(User.full_name).where(User.id == issue.created_by))).scalar_one_or_none()

    message_count = (await db.execute(
        select(func.count(CompanyIssueMessage.id)).where(CompanyIssueMessage.issue_id == issue.id)
    )).scalar() or 0

    last_message_row = (await db.execute(
        select(CompanyIssueMessage.content)
        .where(CompanyIssueMessage.issue_id == issue.id)
        .order_by(CompanyIssueMessage.created_at.desc())
        .limit(1)
    )).first()

    return IssueOut(
        id=issue.id,
        company_id=issue.company_id,
        company_name=company_name,
        title=issue.title,
        status=issue.status,
        created_by=issue.created_by,
        created_by_name=creator_name,
        message_count=message_count,
        last_message=last_message_row[0] if last_message_row else None,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.get("/", response_model=list[IssueOut])
async def list_issues(current_user: CurrentUser, db: DB):
    await _require_issue_role(current_user)

    query = select(CompanyIssue).order_by(CompanyIssue.updated_at.desc())
    if current_user.role == "company_admin":
        if not current_user.company_id:
            raise ForbiddenError()
        query = query.where(CompanyIssue.company_id == current_user.company_id)

    issues = (await db.execute(query)).scalars().all()
    return [await _build_issue_out(db, issue) for issue in issues]


@router.post("/", response_model=IssueDetailOut, status_code=status.HTTP_201_CREATED)
async def create_issue(payload: IssueCreate, current_user: CurrentUser, db: DB):
    if current_user.role != "company_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only company admin can create issues")
    if not current_user.company_id:
        raise ForbiddenError()

    issue = CompanyIssue(
        company_id=current_user.company_id,
        title=payload.title,
        status="open",
        created_by=current_user.id,
    )
    db.add(issue)
    await db.flush()

    initial_message = CompanyIssueMessage(
        issue_id=issue.id,
        author_id=current_user.id,
        content=payload.description,
    )
    db.add(initial_message)

    await db.commit()
    await db.refresh(issue)

    issue_out = await _build_issue_out(db, issue)
    message_out = IssueMessageOut(
        id=initial_message.id,
        issue_id=issue.id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_role=current_user.role,
        content=initial_message.content,
        created_at=initial_message.created_at,
    )
    return IssueDetailOut(**issue_out.model_dump(), messages=[message_out])


@router.get("/{issue_id}", response_model=IssueDetailOut)
async def get_issue(issue_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await _require_issue_role(current_user)

    issue = await _get_issue_or_404(db, issue_id)
    if current_user.role == "company_admin" and issue.company_id != current_user.company_id:
        raise ForbiddenError()

    issue_out = await _build_issue_out(db, issue)

    rows = (await db.execute(
        select(CompanyIssueMessage, User)
        .join(User, User.id == CompanyIssueMessage.author_id)
        .where(CompanyIssueMessage.issue_id == issue.id)
        .order_by(CompanyIssueMessage.created_at.asc())
    )).all()

    messages = [
        IssueMessageOut(
            id=msg.id,
            issue_id=msg.issue_id,
            author_id=msg.author_id,
            author_name=author.full_name,
            author_role=author.role,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg, author in rows
    ]

    return IssueDetailOut(**issue_out.model_dump(), messages=messages)


@router.post("/{issue_id}/messages", response_model=IssueMessageOut, status_code=status.HTTP_201_CREATED)
async def add_issue_message(issue_id: uuid.UUID, payload: IssueMessageCreate, current_user: CurrentUser, db: DB):
    await _require_issue_role(current_user)

    issue = await _get_issue_or_404(db, issue_id)
    if current_user.role == "company_admin" and issue.company_id != current_user.company_id:
        raise ForbiddenError()

    message = CompanyIssueMessage(
        issue_id=issue.id,
        author_id=current_user.id,
        content=payload.content,
    )
    db.add(message)

    issue.updated_at = func.now()

    await db.commit()
    await db.refresh(message)

    return IssueMessageOut(
        id=message.id,
        issue_id=message.issue_id,
        author_id=message.author_id,
        author_name=current_user.full_name,
        author_role=current_user.role,
        content=message.content,
        created_at=message.created_at,
    )
