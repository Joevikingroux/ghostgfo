"""Add sql_connection_ok to evolution_agents

Revision ID: 20260512_0011
Revises: 20260511_0010
Create Date: 2026-05-12
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260512_0011"
down_revision = "20260511_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evolution_agents",
        sa.Column("sql_connection_ok", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evolution_agents", "sql_connection_ok")
