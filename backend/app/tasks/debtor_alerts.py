"""Debtor alert task — reserved for future email-based overdue notifications.

Messaging delivery (WhatsApp/Telegram) has been removed. This task structure
is kept in place for when email-based debtor alerts are implemented.
"""
from __future__ import annotations

from app.core.celery_app import celery


@celery.task(name="ghostcfo.debtor_alerts", bind=True, max_retries=1)
def debtor_alerts_task(self) -> dict:
    return {"sent": 0, "skipped": 0, "reason": "messaging not configured"}
