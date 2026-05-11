"""Add payroll_pending flag to reports.

Revision ID: 20260511_0009
Revises: 20260511_0008
Create Date: 2026-05-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260511_0009"
down_revision = "20260511_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("payroll_pending", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("reports", "payroll_pending")
