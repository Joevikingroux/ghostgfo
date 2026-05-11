"""Telegram Bot webhook receiver.

Telegram calls POST /webhooks/telegram for every update (message, command, etc.).
We use this to:
  - Respond to /start and /chatid commands with the user's chat ID, so they
    can give it to their Numbers10 account manager to add to their company profile.
  - Log delivery confirmations (Telegram doesn't have explicit delivery receipts).

Register the webhook once after deployment:
  curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://ghostcfo.numbers10.co.za/api/webhooks/telegram&secret_token=<WEBHOOK_SECRET>"
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = get_logger(__name__)


@router.post("/telegram", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Receive updates from Telegram Bot API."""
    # Verify the optional secret token if configured
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = str(message.get("chat", {}).get("id", ""))
    text = (message.get("text") or "").strip()
    username = message.get("from", {}).get("username", "")
    first_name = message.get("from", {}).get("first_name", "")

    log.info(
        "telegram_webhook.message",
        chat_id=chat_id[:4] + "****" if chat_id else "",
        text_preview=text[:40],
    )

    # Reply to /start or /chatid with their chat ID
    if text.startswith("/start") or text.startswith("/chatid"):
        name = first_name or username or "there"
        reply = (
            f"👋 Hi {name}! I'm the Ghost CFO bot.\n\n"
            f"Your Telegram Chat ID is:\n\n"
            f"`{chat_id}`\n\n"
            f"Give this number to your Numbers10 account manager and they'll "
            f"link it to your Ghost CFO account. You'll then receive your monthly "
            f"financial reports here."
        )
        await _send_reply(chat_id, reply)

    return {"ok": True}


async def _send_reply(chat_id: str, text: str) -> None:
    """Send a reply message back to a Telegram chat."""
    if not settings.telegram_bot_token:
        return
    import httpx
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
    except Exception as exc:
        log.error("telegram_webhook.reply_failed", error=str(exc))
