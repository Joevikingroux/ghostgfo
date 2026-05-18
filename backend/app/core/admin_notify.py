"""Send internal admin failure notifications via email."""

from __future__ import annotations

import html as _html

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def notify_admin(subject: str, body: str) -> None:
    """Email the admin address. Fire-and-forget — never raises."""
    if not settings.resend_api_key:
        log.warning("admin_notify.skipped", reason="RESEND_API_KEY not set", subject=subject)
        return
    try:
        import resend

        resend.api_key = settings.resend_api_key
        resend.Emails.send(
            {
                "from": f"{settings.from_name} <{settings.from_email}>",
                "to": [settings.admin_email],
                "subject": f"[Ghost CFO Alert] {subject}",
                "html": (
                    f"<p style='font-family:monospace;white-space:pre-wrap'>{_html.escape(body)}</p>"
                    f"<p style='color:#888;font-size:12px'>{_html.escape(settings.brand_footer)}</p>"
                ),
            }
        )
        log.info("admin_notify.sent", subject=subject)
    except Exception as exc:
        log.error("admin_notify.failed", subject=subject, error=str(exc))
