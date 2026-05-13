"""Add pending sync request fields to evolution_agents.

Revision ID: 20260509_0003
Revises: 20260507_0002
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260509_0003"
down_revision = "20260507_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evolution_agents",
        sa.Column("pending_sync_month", sa.Integer(), nullable=True),
    )
    op.add_column(
        "evolution_agents",
        sa.Column("pending_sync_year", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evolution_agents", "pending_sync_year")
    op.drop_column("evolution_agents", "pending_sync_month")
