"""
tasks/ticket_processing.py – Background task for new ticket processing.

Pipeline:
1. Classify category (Groq LLM)
2. Generate embedding (Jina AI)
3. Self-service check (vector similarity → auto-resolve if match)
4. Team routing (category → team mapping)
5. Send notifications
"""
import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.celery_app import celery_app
from app.config import settings
from app.models import AuditLog, Company, NotificationsConfig, Ticket, User
from app.services import ai, notifications, routing, vector

logger = structlog.get_logger(__name__)

# Create a sync-compatible engine for Celery (Celery runs in its own event loop)
def _get_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def _process_ticket_async(ticket_id: str) -> None:
    """Async implementation of the ticket processing pipeline."""
    session_factory = _get_session_factory()

    async with session_factory() as db:
        # ── Fetch ticket ─────────────────────────────────────────────────────
        result = await db.execute(
            select(Ticket).where(Ticket.id == uuid.UUID(ticket_id))
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            logger.error("ticket_not_found", ticket_id=ticket_id)
            return

        logger.info("processing_ticket", ticket_id=ticket_id, title=ticket.title)

        # ── 1. Classify category ─────────────────────────────────────────────
        category = await ai.classify_ticket(ticket.title, ticket.description)
        ticket.category = ai.CATEGORY_DISPLAY.get(category, category)
        logger.info("ticket_classified", ticket_id=ticket_id, category=ticket.category)

        # ── 2. Generate embedding ────────────────────────────────────────────
        combined_text = f"{ticket.title}\n{ticket.description}"
        embedding = await ai.generate_embedding(combined_text)
        ticket.embedding = embedding
        logger.info("ticket_embedded", ticket_id=ticket_id)

        # ── 3. Self-service check ────────────────────────────────────────────
        auto_resolve_result = await vector.find_best_article_for_auto_resolve(
            db, ticket.company_id, embedding
        )

        if auto_resolve_result:
            article, similarity = auto_resolve_result
            ticket.status = "auto_resolved"
            ticket.suggested_article_id = article.id
            ticket.resolved_at = datetime.now(timezone.utc)
            ticket.ai_suggestion = (
                f"This issue was automatically resolved using our knowledge base. "
                f"The article '{article.title}' addresses your problem with "
                f"{int(similarity * 100)}% confidence."
            )
            logger.info(
                "ticket_auto_resolved",
                ticket_id=ticket_id,
                article_id=str(article.id),
                similarity=similarity,
            )

            # Fetch reporter for notification
            reporter_result = await db.execute(
                select(User).where(User.id == ticket.created_by)
            )
            reporter = reporter_result.scalar_one_or_none()

            await notifications.notify_ticket_resolved(
                ticket_number=ticket.ticket_number or ticket_id[:8],
                ticket_title=ticket.title,
                reporter_email=reporter.email if reporter else None,
                resolution_note=f"Knowledge base article: {article.title}",
                frontend_url=settings.FRONTEND_URL,
                auto_resolved=True,
            )

        else:
            # ── 4. Route to team ─────────────────────────────────────────────
            team_name = await routing.resolve_team_for_category(
                db, ticket.company_id, category
            )
            if not team_name:
                team_name = await routing.get_default_team(db, ticket.company_id)

            if team_name:
                ticket.assigned_team = team_name
                ticket.status = "assigned"
            else:
                ticket.status = "new"

            # Generate AI suggestion for the ticket detail view
            suggestion_text, confidence = await ai.generate_ticket_suggestion(
                ticket.title, ticket.description, ticket.category
            )
            ticket.ai_suggestion = f"{suggestion_text} (Confidence: {confidence}%)"

            # ── 5. Notifications ─────────────────────────────────────────────
            # Fetch company + notification config
            company_result = await db.execute(
                select(Company).where(Company.id == ticket.company_id)
            )
            company = company_result.scalar_one_or_none()

            reporter_result = await db.execute(
                select(User).where(User.id == ticket.created_by)
            )
            reporter = reporter_result.scalar_one_or_none()

            # Get notification config for ticket_created event
            notif_result = await db.execute(
                select(NotificationsConfig).where(
                    NotificationsConfig.company_id == ticket.company_id,
                    NotificationsConfig.event_type == "ticket_created",
                )
            )
            notif_config = notif_result.scalar_one_or_none()

            email_recipients = notif_config.email_recipients if notif_config and notif_config.email_enabled else []
            sms_recipients = notif_config.sms_recipients if notif_config and notif_config.sms_enabled else []

            # Always notify the reporter
            if reporter and reporter.email not in email_recipients:
                email_recipients.append(reporter.email)

            await notifications.notify_ticket_created(
                ticket_number=ticket.ticket_number or ticket_id[:8],
                ticket_title=ticket.title,
                reporter_name=reporter.full_name if reporter else "User",
                email_recipients=email_recipients,
                sms_recipients=sms_recipients,
                company_name=company.name if company else "Company",
                frontend_url=settings.FRONTEND_URL,
            )

            if team_name:
                # Get team notification config for ticket_assigned
                assigned_notif_result = await db.execute(
                    select(NotificationsConfig).where(
                        NotificationsConfig.company_id == ticket.company_id,
                        NotificationsConfig.event_type == "ticket_assigned",
                    )
                )
                assigned_notif = assigned_notif_result.scalar_one_or_none()
                assign_emails = assigned_notif.email_recipients if assigned_notif and assigned_notif.email_enabled else []
                assign_sms = assigned_notif.sms_recipients if assigned_notif and assigned_notif.sms_enabled else []

                await notifications.notify_ticket_assigned(
                    ticket_number=ticket.ticket_number or ticket_id[:8],
                    ticket_title=ticket.title,
                    assigned_to_name="Team",
                    team_name=team_name,
                    email_recipients=assign_emails,
                    sms_recipients=assign_sms,
                    company_name=company.name if company else "Company",
                    frontend_url=settings.FRONTEND_URL,
                )

        # ── Audit log ────────────────────────────────────────────────────────
        audit = AuditLog(
            company_id=ticket.company_id,
            action="ticket_processed",
            details={
                "ticket_id": ticket_id,
                "category": ticket.category,
                "status": ticket.status,
                "assigned_team": ticket.assigned_team,
            },
        )
        db.add(audit)

        await db.commit()
        logger.info(
            "ticket_processing_complete",
            ticket_id=ticket_id,
            status=ticket.status,
            team=ticket.assigned_team,
        )


@celery_app.task(
    name="app.tasks.ticket_processing.process_new_ticket",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_new_ticket(self, ticket_id: str) -> dict:
    """
    Celery task: process a newly created ticket.
    Runs the async pipeline in a new event loop.
    """
    try:
        asyncio.run(_process_ticket_async(ticket_id))
        return {"status": "success", "ticket_id": ticket_id}
    except Exception as exc:
        logger.error("ticket_processing_task_failed", ticket_id=ticket_id, error=str(exc))
        raise self.retry(exc=exc)
