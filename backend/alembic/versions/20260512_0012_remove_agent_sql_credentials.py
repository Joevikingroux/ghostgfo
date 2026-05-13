"""Remove db_username and db_password from evolution_agents.

SQL credentials are stored only on the agent's local Windows server (C:\GhostCFO\config.json)
and are never transmitted to or stored on the Ghost CFO server.

Revision ID: 20260512_0012
Revises: 20260512_0011
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260512_0012"
down_revision = "20260512_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("evolution_agents", "db_username")
    op.drop_column("evolution_agents", "db_password")


def downgrade() -> None:
    op.add_column(
        "evolution_agents", sa.Column("db_username", sa.String(255), nullable=True)
    )
    op.add_column(
        "evolution_agents", sa.Column("db_password", sa.String(255), nullable=True)
    )
