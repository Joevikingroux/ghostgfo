"""Add AI usage tracking columns to reports table.

Stamps each report with whether AI (LLM) was used, which model, and total tokens
consumed. Used to identify AI-generated reports and track usage costs.

Revision ID: 20260513_0013
Revises: 20260512_0012
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260513_0013"
down_revision = "20260512_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "ai_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "reports",
        sa.Column("ai_model", sa.String(128), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("ai_tokens_used", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reports", "ai_tokens_used")
    op.drop_column("reports", "ai_model")
    op.drop_column("reports", "ai_generated")
