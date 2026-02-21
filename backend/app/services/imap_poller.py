"""IMAP poller service for email-to-ticket intake (no webhooks).

Behavior:
- Polls IMAP mailbox at a fixed interval
- Reads latest unread email only
- Creates/updates reporter user in mapped company
- Creates ticket with source=email and routes via AI classifier to allowed team categories
"""
import asyncio
import email
import imaplib
import re
import uuid
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr
from typing import Optional, TypedDict

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth.jwt import hash_password
from app.config import settings
from app.models import AuditLog, Team, Ticket, TicketMessage, User
from app.services import ai
from app.services.notifications import notify_ticket_routed

logger = structlog.get_logger(__name__)
DEFAULT_EMAIL_REPORTER_PASSWORD = "12345678"


class EmailPayload(TypedDict):
    message_id: str
    sender_name: str
    sender_email: str
    subject: str
    body: str


def _decode_mime_header(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded: list[str] = []
    for chunk, enc in parts:
        if isinstance(chunk, bytes):
            decoded.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(chunk)
    return "".join(decoded).strip()


def _extract_plain_text(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if content_type == "text/plain" and "attachment" not in disp:
                raw_payload = part.get_payload(decode=True)
                payload = raw_payload if isinstance(raw_payload, bytes) else b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace").strip()

        for part in msg.walk():
            content_type = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if content_type == "text/html" and "attachment" not in disp:
                raw_payload = part.get_payload(decode=True)
                payload = raw_payload if isinstance(raw_payload, bytes) else b""
                charset = part.get_content_charset() or "utf-8"
                html_body = payload.decode(charset, errors="replace")
                text = re.sub(r"<[^>]+>", " ", html_body)
                return re.sub(r"\s+", " ", text).strip()
        return ""

    raw_payload = msg.get_payload(decode=True)
    payload = raw_payload if isinstance(raw_payload, bytes) else b""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace").strip()


def _fetch_latest_unread_email_sync() -> Optional[EmailPayload]:
    if not settings.IMAP_HOST or not settings.IMAP_USERNAME or not settings.IMAP_APP_PASSWORD:
        return None

    imap_cls = imaplib.IMAP4_SSL if settings.IMAP_USE_SSL else imaplib.IMAP4
    connection = imap_cls(settings.IMAP_HOST, settings.IMAP_PORT)
    try:
        connection.login(settings.IMAP_USERNAME, settings.IMAP_APP_PASSWORD)
        connection.select(settings.IMAP_MAILBOX)

        status, data = connection.search(None, "UNSEEN")
        if status != "OK" or not data or not data[0]:
            return None

        msg_ids = data[0].split()
        latest_id = msg_ids[-1]

        fetch_status, msg_data = connection.fetch(latest_id, "(RFC822)")
        if fetch_status != "OK" or not msg_data:
            return None

        raw_bytes = None
        for item in msg_data:
            if isinstance(item, tuple) and len(item) > 1:
                raw_bytes = item[1]
                break
        if not raw_bytes:
            return None

        parsed = email.message_from_bytes(raw_bytes)
        sender_name, sender_email = parseaddr(parsed.get("From", ""))
        sender_email = (sender_email or "").strip().lower()
        subject = _decode_mime_header(parsed.get("Subject")) or "Email Support Request"
        body = _extract_plain_text(parsed)

        connection.store(latest_id, "+FLAGS", "\\Seen")

        return {
            "message_id": _decode_mime_header(parsed.get("Message-ID")) or str(latest_id),
            "sender_name": _decode_mime_header(sender_name),
            "sender_email": sender_email,
            "subject": subject,
            "body": body,
        }
    finally:
        try:
            connection.close()
        except Exception:
            pass
        connection.logout()


def _name_from_email(email_value: str) -> str:
    local = email_value.split("@", 1)[0]
    normalized = re.sub(r"[._-]+", " ", local).strip()
    if not normalized:
        return "Email User"
    return " ".join(part.capitalize() for part in normalized.split())


async def _pick_assignee_for_team(
    db: AsyncSession,
    company_id: uuid.UUID,
    team_name: Optional[str],
) -> Optional[User]:
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


async def poll_imap_and_create_ticket(db: AsyncSession) -> Optional[uuid.UUID]:
    mail = await asyncio.to_thread(_fetch_latest_unread_email_sync)
    if not mail:
        return None

    sender_email = (mail.get("sender_email") or "").strip().lower()
    if not sender_email:
        logger.info("imap_email_skipped", reason="missing_sender")
        return None

    if settings.IMAP_USERNAME and sender_email == settings.IMAP_USERNAME.strip().lower():
        logger.info("imap_email_skipped", reason="self_email")
        return None

    company_admin: Optional[User] = None
    admin_email = settings.IMAP_COMPANY_ADMIN_EMAIL
    if admin_email:
        admin_result = await db.execute(
            select(User).where(User.email == admin_email, User.role == "company_admin")
        )
        company_admin = admin_result.scalar_one_or_none()
    else:
        fallback_result = await db.execute(
            select(User)
            .where(User.role == "company_admin", User.company_id.is_not(None))
            .order_by(User.created_at.asc())
            .limit(1)
        )
        company_admin = fallback_result.scalar_one_or_none()

    if not company_admin or not company_admin.company_id:
        logger.warning("imap_poller_company_admin_not_found", email=admin_email)
        return None

    company_id = company_admin.company_id

    reporter_result = await db.execute(
        select(User).where(User.company_id == company_id, User.email == sender_email)
    )
    reporter = reporter_result.scalar_one_or_none()
    if not reporter:
        reporter = User(
            company_id=company_id,
            email=sender_email,
            hashed_password=hash_password(DEFAULT_EMAIL_REPORTER_PASSWORD),
            full_name=mail.get("sender_name") or _name_from_email(sender_email),
            role="employee",
            status="offline",
            department="Email Support",
        )
        db.add(reporter)
        await db.flush()

    team_result = await db.execute(select(Team).where(Team.company_id == company_id))
    teams = team_result.scalars().all()
    if not teams:
        logger.warning("imap_poller_no_teams", company_id=str(company_id))
        return None

    allowed_categories = [team.name.strip() for team in teams if team.name and team.name.strip()]
    if not allowed_categories:
        return None

    title = (mail.get("subject") or "Email Support Request").strip()[:500]
    body = (mail.get("body") or "").strip()
    if not body:
        body = "Issue reported by email. No body text provided."

    count_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.company_id == company_id)
    )
    count = count_result.scalar() or 0
    ticket_number = f"INC-{count + 1:05d}"

    selected_category = await ai.classify_ticket_to_allowed_category(title, body, allowed_categories)
    if not selected_category:
        selected_category = allowed_categories[0]

    assigned_team = selected_category
    assignee = await _pick_assignee_for_team(db, company_id, assigned_team)

    suggestion_text, confidence = await ai.generate_ticket_suggestion(
        title,
        body,
        selected_category,
    )

    ticket = Ticket(
        company_id=company_id,
        ticket_number=ticket_number,
        title=title,
        description=body,
        status="assigned" if assignee else "new",
        category=selected_category,
        priority="medium",
        assigned_team=assigned_team,
        assigned_to=assignee.id if assignee else None,
        created_by=reporter.id,
        source="email",
        department=assigned_team,
        ai_suggestion=f"{suggestion_text} (Confidence: {confidence}%)",
        ai_confidence=confidence,
        ai_predicted_category=selected_category,
    )
    db.add(ticket)
    await db.flush()

    initial_message = TicketMessage(
        ticket_id=ticket.id,
        author_id=reporter.id,
        author_type="user",
        content=body,
        is_internal=False,
    )
    db.add(initial_message)

    db.add(
        AuditLog(
            company_id=company_id,
            user_id=reporter.id,
            action="ticket_created_from_imap",
            details={
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.ticket_number,
                "sender_email": sender_email,
                "message_id": mail.get("message_id"),
                "assigned_team": assigned_team,
                "assigned_to": str(assignee.id) if assignee else None,
            },
        )
    )

    await db.commit()

    await notify_ticket_routed(
        ticket_number=ticket.ticket_number or str(ticket.id),
        ticket_title=ticket.title,
        reporter_email=reporter.email,
        team_name=ticket.assigned_team,
        assignee_name=assignee.full_name if assignee else None,
        frontend_url=settings.FRONTEND_URL,
    )

    logger.info(
        "imap_ticket_created",
        ticket_id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        sender_email=sender_email,
        team=ticket.assigned_team,
    )
    return ticket.id


async def run_imap_poller(
    stop_event: asyncio.Event,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not settings.IMAP_POLLER_ENABLED:
        logger.info("imap_poller_disabled")
        return

    if not settings.IMAP_HOST or not settings.IMAP_USERNAME or not settings.IMAP_APP_PASSWORD:
        logger.warning("imap_poller_config_incomplete")
        return

    logger.info("imap_poller_started", mailbox=settings.IMAP_MAILBOX, interval=settings.IMAP_POLL_INTERVAL_SECONDS)

    while not stop_event.is_set():
        try:
            async with db_session_factory() as db:
                await poll_imap_and_create_ticket(db)
        except Exception as exc:
            logger.error("imap_poller_cycle_failed", error=str(exc))

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=max(5, settings.IMAP_POLL_INTERVAL_SECONDS))
        except asyncio.TimeoutError:
            continue

    logger.info("imap_poller_stopped")
