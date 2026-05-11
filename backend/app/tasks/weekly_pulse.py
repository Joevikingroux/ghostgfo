"""Weekly cash pulse — reserved for future email-based cash updates.

Messaging delivery (WhatsApp/Telegram) has been removed. This task structure
is kept in place for when email-based weekly pulses are implemented.
"""
from __future__ import annotations

from app.core.celery_app import celery


@celery.task(name="ghostcfo.weekly_pulse", bind=True, max_retries=1)
def weekly_pulse_task(self) -> dict:
    return {"sent": 0, "skipped": 0, "reason": "messaging not configured"}
