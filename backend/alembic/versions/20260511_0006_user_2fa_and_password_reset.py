"""Add 2FA and password-reset columns to users."""
from alembic import op
import sqlalchemy as sa

revision = "20260511_0006"
down_revision = "20260511_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("totp_enrolled_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_token", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_password_reset_token", table_name="users")
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "totp_enrolled_at")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "must_change_password")
