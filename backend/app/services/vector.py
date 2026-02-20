"""
services/vector.py – pgvector similarity search helpers.

Uses cosine distance for knowledge article and ticket similarity queries.
"""
import uuid
from typing import List, Optional, Tuple

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeArticle, Ticket

logger = structlog.get_logger(__name__)

# Cosine similarity threshold for self-service auto-resolve
AUTO_RESOLVE_THRESHOLD = 0.85
# Threshold for showing similar articles in ticket detail
SIMILARITY_THRESHOLD = 0.70


async def find_similar_articles(
    db: AsyncSession,
    company_id: uuid.UUID,
    embedding: List[float],
    limit: int = 5,
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[Tuple[KnowledgeArticle, float]]:
    """
    Find knowledge articles similar to the given embedding vector.
    Returns list of (article, similarity_score) tuples.
    """
    try:
        # pgvector cosine distance: 1 - cosine_similarity
        # Lower distance = higher similarity
        stmt = (
            select(
                KnowledgeArticle,
                (1 - KnowledgeArticle.embedding.cosine_distance(embedding)).label("similarity"),
            )
            .where(
                KnowledgeArticle.company_id == company_id,
                KnowledgeArticle.embedding.is_not(None),
            )
            .order_by(KnowledgeArticle.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        # Filter by threshold
        return [
            (article, float(similarity))
            for article, similarity in rows
            if float(similarity) >= threshold
        ]
    except Exception as e:
        logger.error("vector_search_failed", error=str(e))
        return []


async def find_best_article_for_auto_resolve(
    db: AsyncSession,
    company_id: uuid.UUID,
    embedding: List[float],
) -> Optional[Tuple[KnowledgeArticle, float]]:
    """
    Check if any knowledge article exceeds the auto-resolve threshold.
    Returns (article, similarity) or None.
    """
    results = await find_similar_articles(
        db, company_id, embedding, limit=1, threshold=AUTO_RESOLVE_THRESHOLD
    )
    return results[0] if results else None


async def find_similar_tickets(
    db: AsyncSession,
    company_id: uuid.UUID,
    embedding: List[float],
    exclude_ticket_id: Optional[uuid.UUID] = None,
    limit: int = 5,
) -> List[Tuple[Ticket, float]]:
    """
    Find tickets with similar embeddings (for trend detection and context).
    """
    try:
        stmt = (
            select(
                Ticket,
                (1 - Ticket.embedding.cosine_distance(embedding)).label("similarity"),
            )
            .where(
                Ticket.company_id == company_id,
                Ticket.embedding.is_not(None),
            )
            .order_by(Ticket.embedding.cosine_distance(embedding))
            .limit(limit + 1)
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            (ticket, float(similarity))
            for ticket, similarity in rows
            if exclude_ticket_id is None or ticket.id != exclude_ticket_id
        ][:limit]
    except Exception as e:
        logger.error("similar_tickets_search_failed", error=str(e))
        return []
