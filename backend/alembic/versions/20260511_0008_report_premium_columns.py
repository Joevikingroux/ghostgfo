"""Add narrative_trend and narrative_custom to reports (Premium features).

Revision ID: 20260511_0008
Revises: 20260511_0007
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260511_0008"
down_revision = "20260511_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("narrative_trend", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("narrative_custom", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "narrative_custom")
    op.drop_column("reports", "narrative_trend")
