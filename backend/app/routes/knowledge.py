"""
routes/knowledge.py – Knowledge Base article CRUD endpoints.

Endpoints:
- GET    /knowledge/          List articles (search, category, pagination)
- GET    /knowledge/:id       Get single article (increments view_count)
- POST   /knowledge/          Create article (it_staff+)
- PATCH  /knowledge/:id       Update article (it_staff+)
- DELETE /knowledge/:id       Delete article (company_admin+)
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DB, require_it_staff
from app.models import KnowledgeArticle, User
from app.schemas import ArticleCreate, ArticleListResponse, ArticleOut, ArticleUpdate, ArticleAuthorOut
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _updated_label(dt: datetime) -> str:
    """Convert updated_at to human-readable relative label."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    if delta.total_seconds() < 86400:
        return "Updated today"
    if delta.days == 1:
        return "Updated yesterday"
    if delta.days < 7:
        return f"Updated {delta.days}d ago"
    if delta.days < 30:
        return f"Updated {delta.days // 7}w ago"
    if delta.days < 365:
        return f"Updated {delta.days // 30}mo ago"
    return f"Updated {delta.days // 365}y ago"


def _build_article_out(article: KnowledgeArticle) -> ArticleOut:
    """Build ArticleOut from ORM model."""
    author = None
    if article.author:
        author = ArticleAuthorOut(
            name=article.author.full_name,
            avatar_url=article.author.avatar_url,
        )
    return ArticleOut(
        id=article.id,
        company_id=article.company_id,
        title=article.title,
        content=article.content,
        category=article.category,
        view_count=article.view_count,
        author=author,
        updated_at=article.updated_at,
        created_at=article.created_at,
        updated_label=_updated_label(article.updated_at),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /knowledge/ – List articles
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    current_user: CurrentUser,
    db: DB,
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
):
    """List knowledge articles scoped to the current user's company."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Use super-admin endpoints")

    query = (
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.author))
        .where(KnowledgeArticle.company_id == current_user.company_id)
    )

    if search:
        query = query.where(
            KnowledgeArticle.title.ilike(f"%{search}%")
            | KnowledgeArticle.content.ilike(f"%{search}%")
        )
    if category:
        query = query.where(KnowledgeArticle.category == category)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort by most viewed
    query = query.order_by(KnowledgeArticle.view_count.desc(), KnowledgeArticle.updated_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListResponse(
        articles=[_build_article_out(a) for a in articles],
        total=total,
        page=page,
        limit=limit,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /knowledge/:id – Single article (increments view_count)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Get a single knowledge article and increment its view count."""
    result = await db.execute(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.author))
        .where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article")
    if current_user.company_id and article.company_id != current_user.company_id:
        raise ForbiddenError()

    # Increment view count
    article.view_count = (article.view_count or 0) + 1
    await db.commit()
    await db.refresh(article)

    return _build_article_out(article)


# ─────────────────────────────────────────────────────────────────────────────
# POST /knowledge/ – Create article (it_staff+)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ArticleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_it_staff()],
)
async def create_article(payload: ArticleCreate, current_user: CurrentUser, db: DB):
    """Create a new knowledge article."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Super admins cannot create articles directly")

    article = KnowledgeArticle(
        company_id=current_user.company_id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        author_id=current_user.id,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Reload with author relationship
    result = await db.execute(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.author))
        .where(KnowledgeArticle.id == article.id)
    )
    article = result.scalar_one()
    return _build_article_out(article)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /knowledge/:id – Update article (it_staff+)
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{article_id}",
    response_model=ArticleOut,
    dependencies=[require_it_staff()],
)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    current_user: CurrentUser,
    db: DB,
):
    """Update an existing knowledge article."""
    result = await db.execute(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.author))
        .where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article")
    if current_user.company_id and article.company_id != current_user.company_id:
        raise ForbiddenError()

    if payload.title is not None:
        article.title = payload.title
    if payload.content is not None:
        article.content = payload.content
    if payload.category is not None:
        article.category = payload.category

    await db.commit()
    await db.refresh(article)
    return _build_article_out(article)


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /knowledge/:id – Delete article (company_admin+)
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Delete a knowledge article. Requires company_admin or super_admin."""
    if current_user.role not in ("company_admin", "super_admin"):
        raise ForbiddenError("Requires company_admin or super_admin role")

    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article")
    if current_user.company_id and article.company_id != current_user.company_id:
        raise ForbiddenError()

    await db.delete(article)
    await db.commit()
