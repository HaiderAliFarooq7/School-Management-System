"""parent module tenant tables: accounts, devices, notifications, log

Adds the parent companion app's per-school tables. This migration runs against
every tenant (school) database through the existing provisioning + startup
migration path (bootstrap.init_master → run_migrations per school), so every
school gets these tables with no manual step.

Additive only — no existing table is touched, so staff functionality is
unaffected. The master-side routing table (parent_directory) is created
separately via the master metadata (db.master.init_master_schema), matching how
schools / master_users / user_directory are managed.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parent_account",
        sa.Column("parent_id", sa.Integer(), primary_key=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("mobile_number", name="uq_parent_account_mobile"),
    )
    op.create_index("ix_parent_account_mobile_number", "parent_account", ["mobile_number"])

    op.create_table(
        "parent_device",
        sa.Column("device_id", sa.Integer(), primary_key=True),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("fcm_token", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=20), server_default="android"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.parent_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("fcm_token", name="uq_parent_device_token"),
    )
    op.create_index("ix_parent_device_parent_id", "parent_device", ["parent_id"])

    op.create_table(
        "parent_notification",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("notif_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.parent_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["student.student_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_parent_notification_parent_id", "parent_notification", ["parent_id"])
    op.create_index("ix_parent_notification_created_at", "parent_notification", ["created_at"])

    op.create_table(
        "notification_log",
        sa.Column("log_id", sa.Integer(), primary_key=True),
        sa.Column("notif_type", sa.String(length=30), nullable=False),
        sa.Column("audience", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("class_name", sa.String(length=50), nullable=True),
        sa.Column("sent_by_user_id", sa.Integer(), nullable=True),
        sa.Column("recipients_count", sa.Integer(), server_default="0"),
        sa.Column("delivered_count", sa.Integer(), server_default="0"),
        sa.Column("failed_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["student.student_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sent_by_user_id"], ["user_account.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_notification_log_created_at", "notification_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_log_created_at", table_name="notification_log")
    op.drop_table("notification_log")
    op.drop_index("ix_parent_notification_created_at", table_name="parent_notification")
    op.drop_index("ix_parent_notification_parent_id", table_name="parent_notification")
    op.drop_table("parent_notification")
    op.drop_index("ix_parent_device_parent_id", table_name="parent_device")
    op.drop_table("parent_device")
    op.drop_index("ix_parent_account_mobile_number", table_name="parent_account")
    op.drop_table("parent_account")
