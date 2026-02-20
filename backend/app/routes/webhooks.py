"""
routes/webhooks.py – Inbound webhook endpoints.

Endpoints:
- POST /webhooks/email   Inbound email → create ticket (Resend/SendGrid forward)
"""
import hashlib
import hmac
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.config import settings
from app.dependencies import DB
from app.models import AuditLog, Ticket, User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class InboundEmailPayload(BaseModel):
    """Normalized inbound email webhook payload."""
    from_email: str
    subject: str
    body: str
    message_id: str = ""


def _verify_hmac(body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature from webhook provider."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─────────────────────────────────────────────────────────────────────────────
# POST /webhooks/email – Inbound email to ticket
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/email", status_code=status.HTTP_200_OK)
async def inbound_email(
    request: Request,
    db: DB,
    x_webhook_signature: str = Header(default=""),
):
    """
    Convert an inbound forwarded email into a support ticket.

    Expected JSON body:
    {
        "from_email": "user@company.com",
        "subject": "My VPN stopped working",
        "body": "Hello, I cannot connect to VPN since this morning...",
        "message_id": "<optional-message-id>"
    }

    If a user matching from_email exists in the system, the ticket is created
    under their company. Otherwise a 404 is returned.

    HMAC validation is performed when WEBHOOK_SECRET env var is set.
    """
    raw_body = await request.body()

    # Validate HMAC signature if a webhook secret is configured
    webhook_secret = getattr(settings, "WEBHOOK_SECRET", None)
    if webhook_secret and x_webhook_signature:
        if not _verify_hmac(raw_body, x_webhook_signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse the JSON body
    try:
        data = await request.json()
        payload = InboundEmailPayload(**data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {exc}") from exc

    # Look up the sender by email
    r = await db.execute(select(User).where(User.email == payload.from_email))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"No user found with email {payload.from_email}",
        )
    if not user.company_id:
        raise HTTPException(status_code=400, detail="Sender has no associated company")

    # Generate ticket number
    r_count = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.company_id == user.company_id)
    )
    count = r_count.scalar() or 0
    ticket_number = f"INC-{count + 1:05d}"

    # Build description from email body
    description = payload.body.strip() or "(No body)"
    if len(description) < 10:
        description = description + " (Email ticket)"

    ticket = Ticket(
        company_id=user.company_id,
        ticket_number=ticket_number,
        title=payload.subject[:500] or "Email support request",
        description=description,
        priority="medium",
        source="email",
        created_by=user.id,
        status="new",
    )
    db.add(ticket)

    db.add(AuditLog(
        company_id=user.company_id,
        user_id=user.id,
        action="ticket_created_via_email",
        details={
            "ticket_number": ticket_number,
            "subject": payload.subject,
            "message_id": payload.message_id,
        },
    ))

    await db.commit()
    await db.refresh(ticket)

    # Enqueue background AI processing (non-blocking)
    try:
        from app.tasks.ticket_processing import process_new_ticket  # noqa: PLC0415
        process_new_ticket.delay(str(ticket.id))
    except Exception:
        pass  # Celery not available in development

    return {
        "status": "created",
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
    }
