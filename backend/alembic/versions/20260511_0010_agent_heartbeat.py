"""Add last_heartbeat_at to evolution_agents

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-11
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260511_0010"
down_revision = "20260511_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evolution_agents",
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evolution_agents", "last_heartbeat_at")
