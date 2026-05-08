"""initial schema

Revision ID: 20260507_0001
Revises:
Create Date: 2026-05-07
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260507_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trading_name", sa.String(255)),
        sa.Column("reg_number", sa.String(64)),
        sa.Column("vat_number", sa.String(64)),
        sa.Column("industry", sa.String(128)),
        sa.Column("owner_name", sa.String(255)),
        sa.Column("owner_email", sa.String(255)),
        sa.Column("owner_whatsapp", sa.String(32)),
        sa.Column("bookkeeper_name", sa.String(255)),
        sa.Column("bookkeeper_email", sa.String(255)),
        sa.Column("plan", sa.String(32), nullable=False, server_default="starter"),
        sa.Column("plan_start_date", sa.Date()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="partner"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "evolution_agents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("api_key", sa.String(128), nullable=False, unique=True),
        sa.Column("server_name", sa.String(255)),
        sa.Column("db_name", sa.String(255)),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("last_sync_status", sa.String(32)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "uploads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
        ),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("income_statement_path", sa.Text()),
        sa.Column("balance_sheet_path", sa.Text()),
        sa.Column("debtors_age_path", sa.Text()),
        sa.Column("creditors_age_path", sa.Text()),
        sa.Column("payroll_summary_path", sa.Text()),
        sa.Column("payroll_employee_cost_path", sa.Text()),
        sa.Column("payroll_leave_path", sa.Text()),
        sa.Column("payroll_journal_path", sa.Text()),
        sa.Column(
            "payroll_journal_integrated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "upload_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploads.id"),
        ),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column(
            "metrics", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("narrative_summary", sa.Text()),
        sa.Column("narrative_revenue", sa.Text()),
        sa.Column("narrative_costs", sa.Text()),
        sa.Column("narrative_debtors", sa.Text()),
        sa.Column("narrative_payroll", sa.Text()),
        sa.Column("narrative_cash", sa.Text()),
        sa.Column("narrative_actions", sa.Text()),
        sa.Column("pdf_path", sa.Text()),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_sent_at", sa.DateTime(timezone=True)),
        sa.Column(
            "whatsapp_sent", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("whatsapp_sent_at", sa.DateTime(timezone=True)),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "company_id", "period_month", "period_year", name="uq_report_period"
        ),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("uploads")
    op.drop_table("users")
    op.drop_table("evolution_agents")
    op.drop_table("companies")
