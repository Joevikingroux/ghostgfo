"""Celery application — background report generation and scheduled tasks."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "ghostcfo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.generate_report",
        "app.tasks.deliver_report",
        "app.tasks.weekly_pulse",
        "app.tasks.debtor_alerts",
        "app.tasks.cleanup_pending",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Johannesburg",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=15 * 60,
    task_soft_time_limit=12 * 60,
    worker_max_tasks_per_child=50,
    # ---- Celery Beat periodic schedule ----
    beat_schedule={
        # Check all active clients daily at 08:00 SAST and send email
        # alerts for any invoices that have crossed the 61-day mark.
        "debtor-alerts-daily": {
            "task": "ghostcfo.debtor_alerts",
            "schedule": crontab(hour=8, minute=0),
        },
        # Monday morning cash pulse for Professional + Premium plans.
        "weekly-pulse-monday": {
            "task": "ghostcfo.weekly_pulse",
            "schedule": crontab(hour=7, minute=0, day_of_week=1),
        },
        # Purge abandoned signup accounts every 30 minutes.
        # Pending companies (payment never completed) older than 2 hours are deleted.
        "cleanup-pending-every-30m": {
            "task": "ghostcfo.cleanup_pending",
            "schedule": crontab(minute="*/30"),
        },
    },
)
