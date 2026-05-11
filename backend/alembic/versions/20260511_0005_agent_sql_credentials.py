"""Add SQL credentials to evolution_agents.

Revision ID: 20260511_0005
Revises: 20260509_0004
Create Date: 2026-05-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260511_0005"
down_revision = "20260509_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evolution_agents", sa.Column("db_username", sa.String(255), nullable=True))
    op.add_column("evolution_agents", sa.Column("db_password", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("evolution_agents", "db_password")
    op.drop_column("evolution_agents", "db_username")
