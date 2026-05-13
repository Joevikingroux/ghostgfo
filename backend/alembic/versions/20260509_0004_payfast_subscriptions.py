"""Add PayFast subscription fields to companies.

Revision ID: 20260509_0004
Revises: 20260509_0003
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260509_0004"
down_revision = "20260509_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("payfast_token", sa.Text(), nullable=True))
    op.add_column(
        "companies",
        sa.Column(
            "subscription_status",
            sa.String(32),
            nullable=False,
            server_default="inactive",
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "subscription_status")
    op.drop_column("companies", "payfast_token")
