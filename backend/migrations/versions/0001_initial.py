"""initial CareerSetu schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "analysis_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False, server_default="Job-fit analysis"),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("ats_coverage", sa.Integer(), nullable=False),
        sa.Column("recommendation", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_analysis_records_user_id", "analysis_records", ["user_id"], unique=False)

    op.create_table(
        "interview_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_quality", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("next_difficulty", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("improvements", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_interview_attempts_user_id", "interview_attempts", ["user_id"], unique=False)

    op.create_table(
        "roadmap_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_roadmap_records_user_id", "roadmap_records", ["user_id"], unique=True)


def downgrade():
    op.drop_index("ix_roadmap_records_user_id", table_name="roadmap_records")
    op.drop_table("roadmap_records")
    op.drop_index("ix_interview_attempts_user_id", table_name="interview_attempts")
    op.drop_table("interview_attempts")
    op.drop_index("ix_analysis_records_user_id", table_name="analysis_records")
    op.drop_table("analysis_records")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
