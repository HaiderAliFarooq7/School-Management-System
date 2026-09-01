"""expense: school expenses and staff salaries

Additive tenant table. Applied to every school database via the startup
migration path. Records money going out (salaries, utilities, rent, supplies)
so the admin can see real profit/loss against fee collections rather than
income alone.

Revision ID: a1b2c3d4e5f7
Revises: d1e2f3a4b5c6
Create Date: 2026-09-01 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expense",
        sa.Column("expense_id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), server_default=""),
        sa.Column("paid_to", sa.String(length=120), server_default=""),
        sa.Column("for_month", sa.String(length=7), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(length=30), server_default="Cash"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("recorded_by_username", sa.String(length=50), server_default=""),
    )
    op.create_index("ix_expense_created_at", "expense", ["created_at"])
    op.create_index("ix_expense_expense_date", "expense", ["expense_date"])
    op.create_index("ix_expense_category", "expense", ["category"])


def downgrade() -> None:
    op.drop_index("ix_expense_category", table_name="expense")
    op.drop_index("ix_expense_expense_date", table_name="expense")
    op.drop_index("ix_expense_created_at", table_name="expense")
    op.drop_table("expense")
