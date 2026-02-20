"""
services/notifications.py – Email (Resend) and SMS (Twilio) notifications.

Gracefully degrades to logging when API keys are not configured.
"""
from typing import List, Optional

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Email via Resend
# ─────────────────────────────────────────────────────────────────────────────

async def send_email(
    to: List[str],
    subject: str,
    html_body: str,
    reply_to: Optional[str] = None,
) -> bool:
    """
    Send an email via Resend SDK.
    Falls back to logging if RESEND_API_KEY is not set.
    """
    if not to:
        return False

    if not settings.RESEND_API_KEY:
        logger.info(
            "email_mock_sent",
            to=to,
            subject=subject,
            note="Set RESEND_API_KEY to send real emails",
        )
        return True

    try:
        import resend  # noqa: PLC0415

        resend.api_key = settings.RESEND_API_KEY

        params = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": to,
            "subject": subject,
            "html": html_body,
        }
        if reply_to:
            params["reply_to"] = reply_to

        resend.Emails.send(params)
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as e:
        logger.error("email_send_failed", error=str(e), to=to)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# SMS via Twilio
# ─────────────────────────────────────────────────────────────────────────────

async def send_sms(to: List[str], body: str) -> bool:
    """
    Send an SMS via Twilio.
    Mocked if Twilio credentials are not set.
    """
    if not to:
        return False

    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.info(
            "sms_mock_sent",
            to=to,
            body=body[:50],
            note="Set TWILIO_* env vars to send real SMS",
        )
        return True

    try:
        from twilio.rest import Client  # noqa: PLC0415

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        for phone in to:
            client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )
        logger.info("sms_sent", to=to)
        return True
    except Exception as e:
        logger.error("sms_send_failed", error=str(e))
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Event-specific notification builders
# ─────────────────────────────────────────────────────────────────────────────

async def notify_ticket_created(
    ticket_number: str,
    ticket_title: str,
    reporter_name: str,
    email_recipients: List[str],
    sms_recipients: List[str],
    company_name: str,
    frontend_url: str,
) -> None:
    """Send notifications when a ticket is created."""
    ticket_url = f"{frontend_url}/tickets/{ticket_number}"

    html = f"""
    <h2>New Support Ticket Created</h2>
    <p><strong>Company:</strong> {company_name}</p>
    <p><strong>Ticket:</strong> {ticket_number}</p>
    <p><strong>Title:</strong> {ticket_title}</p>
    <p><strong>Reported by:</strong> {reporter_name}</p>
    <p><a href="{ticket_url}">View Ticket →</a></p>
    """
    sms = f"[{company_name}] New ticket {ticket_number}: {ticket_title[:60]}"

    await send_email(email_recipients, f"[{ticket_number}] New Ticket: {ticket_title}", html)
    await send_sms(sms_recipients, sms)


async def notify_ticket_assigned(
    ticket_number: str,
    ticket_title: str,
    assigned_to_name: str,
    team_name: Optional[str],
    email_recipients: List[str],
    sms_recipients: List[str],
    company_name: str,
    frontend_url: str,
) -> None:
    """Send notifications when a ticket is assigned."""
    ticket_url = f"{frontend_url}/tickets/{ticket_number}"
    team_info = f" (Team: {team_name})" if team_name else ""

    html = f"""
    <h2>Ticket Assigned</h2>
    <p><strong>Ticket:</strong> {ticket_number} - {ticket_title}</p>
    <p><strong>Assigned to:</strong> {assigned_to_name}{team_info}</p>
    <p><a href="{ticket_url}">View Ticket →</a></p>
    """
    sms = f"[{company_name}] Ticket {ticket_number} assigned to {assigned_to_name}"

    await send_email(email_recipients, f"[{ticket_number}] Ticket Assigned: {ticket_title}", html)
    await send_sms(sms_recipients, sms)


async def notify_ticket_resolved(
    ticket_number: str,
    ticket_title: str,
    reporter_email: Optional[str],
    resolution_note: Optional[str],
    frontend_url: str,
    auto_resolved: bool = False,
) -> None:
    """Send resolution notification to the ticket reporter."""
    if not reporter_email:
        return

    ticket_url = f"{frontend_url}/tickets/{ticket_number}"
    resolution_info = ""
    if resolution_note:
        resolution_info = f"<p><strong>Resolution:</strong> {resolution_note}</p>"
    auto_tag = " (AI Self-Service)" if auto_resolved else ""

    html = f"""
    <h2>Your Ticket Has Been Resolved{auto_tag}</h2>
    <p><strong>Ticket:</strong> {ticket_number}</p>
    <p><strong>Title:</strong> {ticket_title}</p>
    {resolution_info}
    <p><a href="{ticket_url}">View Ticket →</a></p>
    <p>If this resolution didn't help, please reply to this email or reopen the ticket.</p>
    """
    await send_email(
        [reporter_email],
        f"[{ticket_number}] Resolved: {ticket_title}",
        html,
    )
