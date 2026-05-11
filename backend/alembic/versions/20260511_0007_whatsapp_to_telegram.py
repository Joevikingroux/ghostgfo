"""Rename WhatsApp columns to Telegram across companies and reports tables.

Revision ID: 20260511_0007
Revises: 20260511_0006
"""
from __future__ import annotations

from alembic import op

revision = "20260511_0007"
down_revision = "20260511_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("companies", "owner_whatsapp", new_column_name="owner_telegram")
    op.alter_column("reports", "whatsapp_sent", new_column_name="telegram_sent")
    op.alter_column("reports", "whatsapp_sent_at", new_column_name="telegram_sent_at")


def downgrade() -> None:
    op.alter_column("companies", "owner_telegram", new_column_name="owner_whatsapp")
    op.alter_column("reports", "telegram_sent", new_column_name="whatsapp_sent")
    op.alter_column("reports", "telegram_sent_at", new_column_name="whatsapp_sent_at")
