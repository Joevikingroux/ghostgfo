"""Add language column to companies table.

Revision ID: 20260507_0002
Revises: 20260507_0001
Create Date: 2026-05-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260507_0002"
down_revision = "20260507_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("companies", "language")
