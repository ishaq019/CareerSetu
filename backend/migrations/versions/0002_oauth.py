"""add Google OAuth identity columns to users

Revision ID: 0002_oauth
Revises: 0001_initial
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_oauth"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # batch_alter_table makes these changes work on SQLite as well as Postgres.
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "auth_provider",
                sa.String(length=32),
                nullable=False,
                server_default="password",
            )
        )
        batch.add_column(sa.Column("google_sub", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("full_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("avatar_url", sa.String(length=512), nullable=True))
        # OAuth accounts have no local password.
        batch.alter_column("password_hash", existing_type=sa.String(length=512), nullable=True)

    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)


def downgrade():
    op.drop_index("ix_users_google_sub", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("password_hash", existing_type=sa.String(length=512), nullable=False)
        batch.drop_column("avatar_url")
        batch.drop_column("full_name")
        batch.drop_column("google_sub")
        batch.drop_column("auth_provider")
