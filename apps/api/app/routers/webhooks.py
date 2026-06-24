import hashlib
import hmac
import json

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException

router = APIRouter(tags=["webhooks"])
settings = get_settings()


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

    # Verify HMAC signature
    if settings.whatsapp_app_secret and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            settings.whatsapp_app_secret.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise ForbiddenException("Invalid webhook signature")

    payload = json.loads(body_bytes)

    # Route to message handler
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
    """
    Process inbound WhatsApp message.
    TODO: match to merchant by phone_number_id, create order from text/media.
    """
    pass
