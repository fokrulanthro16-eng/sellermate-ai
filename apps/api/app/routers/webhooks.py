from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, desc, func

from app.core.config import get_settings
from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.webhook_event import WebhookEvent

router = APIRouter(tags=["webhooks"])
settings = get_settings()


# ── WhatsApp ──────────────────────────────────────────────────────────────────

@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    """Meta webhook verification handshake."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return PlainTextResponse(content=challenge or "", status_code=status.HTTP_200_OK)

    raise ForbiddenException("Webhook verification failed")


@router.post("/whatsapp", status_code=200)
async def receive_whatsapp(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
):
    """Receive inbound WhatsApp messages from Meta Cloud API."""
    body_bytes = await request.body()

    if settings.whatsapp_app_secret and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            settings.whatsapp_app_secret.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise ForbiddenException("Invalid webhook signature")

    payload = json.loads(body_bytes)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                await _handle_inbound_message(
                    phone_number_id=value.get("metadata", {}).get("phone_number_id"),
                    from_phone=message.get("from"),
                    message_type=message.get("type"),
                    message=message,
                )

    return {"status": "ok"}


async def _handle_inbound_message(
    phone_number_id: str | None,
    from_phone: str | None,
    message_type: str | None,
    message: dict,
) -> None:
    pass


# ── Generic provider receive ──────────────────────────────────────────────────

@router.post("/{provider}/receive", status_code=200)
async def receive_provider_webhook(
    provider: str,
    request: Request,
    db: DB,
    x_signature: str | None = Header(None),
    x_hub_signature_256: str | None = Header(None),
):
    """Store incoming webhook from any integration provider (mock: signature verification skipped)."""
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes)
    except Exception:
        payload = {"raw": body_bytes.decode("utf-8", errors="replace")}

    sig = x_signature or x_hub_signature_256
    event_type = str(
        payload.get("event")
        or payload.get("type")
        or payload.get("event_type")
        or payload.get("eventType")
        or "unknown"
    )

    event = WebhookEvent(
        provider=provider,
        event_type=event_type,
        payload=payload,
        signature=sig,
        status="pending",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {"status": "received", "event_id": event.id}


# ── Event list and retry ──────────────────────────────────────────────────────

def _event_dict(e: WebhookEvent) -> dict:
    return {
        "id": e.id,
        "provider": e.provider,
        "event_type": e.event_type,
        "status": e.status,
        "retry_count": e.retry_count,
        "error_message": e.error_message,
        "received_at": e.received_at.isoformat() if e.received_at else None,
        "processed_at": e.processed_at.isoformat() if e.processed_at else None,
    }


@router.get("/events")
async def list_webhook_events(
    merchant: CurrentMerchant,
    db: DB,
    provider: str | None = None,
    event_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    q = select(WebhookEvent).order_by(desc(WebhookEvent.received_at))
    if provider:
        q = q.where(WebhookEvent.provider == provider)
    if event_status:
        q = q.where(WebhookEvent.status == event_status)
    q = q.offset(offset).limit(limit)

    result = await db.execute(q)
    events = result.scalars().all()

    total_q = select(func.count()).select_from(WebhookEvent)
    if provider:
        total_q = total_q.where(WebhookEvent.provider == provider)
    total_r = await db.execute(total_q)
    total = total_r.scalar() or 0

    return {
        "success": True,
        "data": {"items": [_event_dict(e) for e in events], "total": total},
    }


@router.post("/events/{event_id}/retry")
async def retry_webhook_event(
    event_id: str,
    merchant: CurrentMerchant,
    db: DB,
):
    result = await db.execute(select(WebhookEvent).where(WebhookEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise NotFoundException("Webhook event not found")

    event.status = "processed"
    event.retry_count += 1
    event.processed_at = datetime.now(tz=timezone.utc)
    event.error_message = None
    await db.commit()
    await db.refresh(event)

    return {"success": True, "data": _event_dict(event)}
