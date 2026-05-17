"""Change uploads.uploaded_by FK to ON DELETE SET NULL.

Previously the FK had no ON DELETE action, causing a constraint violation when
deleting a company (which cascades to users, which are still referenced by
uploads.uploaded_by).

Revision ID: 20260513_0014
Revises: 20260513_0013
Create Date: 2026-05-13
"""

from __future__ import annotations

from alembic import op

revision = "20260513_0014"
down_revision = "20260513_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old FK, re-add with ON DELETE SET NULL
    op.drop_constraint("uploads_uploaded_by_fkey", "uploads", type_="foreignkey")
    op.create_foreign_key(
        "uploads_uploaded_by_fkey",
        "uploads",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("uploads_uploaded_by_fkey", "uploads", type_="foreignkey")
    op.create_foreign_key(
        "uploads_uploaded_by_fkey",
        "uploads",
        "users",
        ["uploaded_by"],
        ["id"],
    )
