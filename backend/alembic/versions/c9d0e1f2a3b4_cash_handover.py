"""cash_handover: cash handed over by accountants to the admin

Additive tenant table. Applied to every school database via the startup
migration path. Records how much physical cash each accountant handed in, so
the admin can reconcile it against what they collected (from fee_audit_log).

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_handover",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("accountant_user_id", sa.Integer(), nullable=True),
        sa.Column("accountant_username", sa.String(length=50), server_default=""),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("handover_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("recorded_by_username", sa.String(length=50), server_default=""),
    )
    op.create_index("ix_cash_handover_created_at", "cash_handover", ["created_at"])
    op.create_index("ix_cash_handover_accountant_user_id", "cash_handover", ["accountant_user_id"])


def downgrade() -> None:
    op.drop_index("ix_cash_handover_accountant_user_id", table_name="cash_handover")
    op.drop_index("ix_cash_handover_created_at", table_name="cash_handover")
    op.drop_table("cash_handover")
