"""
tasks/trend_detection.py – Periodic background task for clustering related tickets.

Uses DBSCAN on ticket embeddings to detect issue trends per company.
Generates a summary for each cluster using Groq LLM.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.celery_app import celery_app
from app.config import settings
from app.models import Company, Ticket, TrendCluster
from app.services.ai import summarize_trend_cluster

logger = structlog.get_logger(__name__)


def _get_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def _detect_trends_for_company(
    db: AsyncSession, company_id: uuid.UUID, company_name: str
) -> int:
    """
    Detect ticket clusters for a single company.
    Returns the number of clusters found.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.TREND_LOOKBACK_HOURS)

    # Fetch recent unresolved tickets with embeddings
    result = await db.execute(
        select(Ticket).where(
            Ticket.company_id == company_id,
            Ticket.status.notin_(["resolved", "closed", "auto_resolved"]),
            Ticket.created_at >= cutoff,
            Ticket.embedding.is_not(None),
        )
    )
    tickets = result.scalars().all()

    if len(tickets) < settings.TREND_MIN_CLUSTER_SIZE:
        logger.info(
            "insufficient_tickets_for_clustering",
            company_id=str(company_id),
            count=len(tickets),
        )
        return 0

    logger.info(
        "clustering_tickets",
        company=company_name,
        ticket_count=len(tickets),
    )

    # Build embedding matrix
    try:
        from sklearn.cluster import DBSCAN  # noqa: PLC0415
        from sklearn.preprocessing import normalize  # noqa: PLC0415

        embeddings = np.array([t.embedding for t in tickets], dtype=np.float32)
        # Normalize for cosine similarity (then use euclidean distance = cosine distance)
        embeddings_norm = normalize(embeddings)

        # DBSCAN: eps=0.3 ≈ cosine similarity of 0.7
        clustering = DBSCAN(eps=0.3, min_samples=settings.TREND_MIN_CLUSTER_SIZE, metric="euclidean")
        labels = clustering.fit_predict(embeddings_norm)

        clusters_found = 0
        unique_labels = set(labels)
        unique_labels.discard(-1)  # -1 is noise

        for label in unique_labels:
            cluster_tickets = [t for t, lbl in zip(tickets, labels) if lbl == label]
            if len(cluster_tickets) < settings.TREND_MIN_CLUSTER_SIZE:
                continue

            ticket_ids = [str(t.id) for t in cluster_tickets]
            titles = [t.title for t in cluster_tickets]

            # Generate summary
            summary = await summarize_trend_cluster(titles)

            # Detect dominant category
            categories = [t.category for t in cluster_tickets if t.category]
            dominant_category = max(set(categories), key=categories.count) if categories else None

            # Save cluster
            cluster = TrendCluster(
                company_id=company_id,
                ticket_ids=ticket_ids,
                summary=summary,
                category=dominant_category,
                ticket_count=len(cluster_tickets),
            )
            db.add(cluster)
            clusters_found += 1

            logger.info(
                "trend_cluster_created",
                company=company_name,
                cluster_size=len(cluster_tickets),
                category=dominant_category,
            )

        await db.commit()
        return clusters_found

    except ImportError:
        logger.warning("scikit_learn_not_available", note="Install scikit-learn for trend detection")
        return 0
    except Exception as e:
        logger.error("trend_detection_failed", company=company_name, error=str(e))
        return 0


async def _detect_trends_async() -> dict:
    """Run trend detection for all companies."""
    session_factory = _get_session_factory()
    results = {}

    async with session_factory() as db:
        # Fetch all active companies
        company_result = await db.execute(
            select(Company).where(Company.status == "active")
        )
        companies = company_result.scalars().all()

        for company in companies:
            count = await _detect_trends_for_company(db, company.id, company.name)
            results[company.name] = count

    return results


@celery_app.task(
    name="app.tasks.trend_detection.detect_trends_all_companies",
    bind=True,
    max_retries=2,
)
def detect_trends_all_companies(self) -> dict:
    """
    Celery periodic task: detect issue trends across all companies.
    Scheduled hourly via Celery Beat.
    """
    try:
        results = asyncio.run(_detect_trends_async())
        logger.info("trend_detection_complete", results=results)
        return {"status": "success", "results": results}
    except Exception as exc:
        logger.error("trend_detection_task_failed", error=str(exc))
        raise self.retry(exc=exc)
