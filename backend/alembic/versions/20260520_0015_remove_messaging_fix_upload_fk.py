"""Remove messaging columns and fix reports.upload_id FK.

- Drop telegram_sent, telegram_sent_at from reports
- Drop owner_telegram from companies
- Fix reports.upload_id FK to ON DELETE SET NULL
  (previously had no ondelete action, causing FK violation when deleting uploads)

Revision ID: 20260520_0015
Revises: 20260513_0014
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260520_0015"
down_revision = "20260513_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop messaging columns from reports
    op.drop_column("reports", "telegram_sent")
    op.drop_column("reports", "telegram_sent_at")

    # Drop messaging column from companies
    op.drop_column("companies", "owner_telegram")

    # Fix reports.upload_id FK: drop existing constraint, re-add with SET NULL
    op.drop_constraint("reports_upload_id_fkey", "reports", type_="foreignkey")
    op.create_foreign_key(
        "reports_upload_id_fkey",
        "reports",
        "uploads",
        ["upload_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Restore reports.upload_id FK without ondelete
    op.drop_constraint("reports_upload_id_fkey", "reports", type_="foreignkey")
    op.create_foreign_key(
        "reports_upload_id_fkey",
        "reports",
        "uploads",
        ["upload_id"],
        ["id"],
    )

    # Restore columns
    op.add_column(
        "companies",
        sa.Column("owner_telegram", sa.String(32), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column(
            "telegram_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "reports",
        sa.Column("telegram_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
