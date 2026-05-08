"""Meta WhatsApp Cloud API webhook receiver.

Handles:
  - GET  /webhooks/whatsapp  — hub verification challenge (Meta registration)
  - POST /webhooks/whatsapp  — delivery status updates and inbound messages
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = get_logger(__name__)


@router.get("/whatsapp", response_class=PlainTextResponse)
def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
):
    """Meta calls this once when you register the webhook URL."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        log.info("whatsapp_webhook.verified")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def whatsapp_events(request: Request):
    """Receive delivery receipts and inbound messages from Meta."""
    try:
        data = await request.json()
    except Exception:
        return {"status": "ok"}

    entry = data.get("entry", [])
    for e in entry:
        for change in e.get("changes", []):
            value = change.get("value", {})

            # Delivery status updates
            for status_update in value.get("statuses", []):
                wa_id = status_update.get("id")
                wa_status = status_update.get("status")
                recipient = status_update.get("recipient_id", "")
                log.info(
                    "whatsapp_webhook.status",
                    wa_id=wa_id,
                    status=wa_status,
                    recipient=recipient[:6] + "****" if recipient else "",
                )
                # Phase 5: update per-message delivery log here

            # Inbound messages (not handled in Phase 3)
            for msg in value.get("messages", []):
                log.info(
                    "whatsapp_webhook.inbound",
                    type=msg.get("type"),
                    from_=str(msg.get("from", ""))[:6] + "****",
                )

    return {"status": "ok"}
