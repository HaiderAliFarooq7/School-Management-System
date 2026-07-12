"""fee_audit_log: per-user trail of fee payment/discount/edit/delete actions

Additive tenant table. Applied to every school database via the startup
migration path. Kept indefinitely (well beyond the required 3 months).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fee_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_username", sa.String(length=50), server_default=""),
        sa.Column("actor_role", sa.String(length=30), server_default=""),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("student_name", sa.String(length=150), server_default=""),
        sa.Column("label", sa.String(length=120), server_default=""),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_fee_audit_log_created_at", "fee_audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_fee_audit_log_created_at", table_name="fee_audit_log")
    op.drop_table("fee_audit_log")
