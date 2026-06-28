"""add discount_amount/discount_reason to fee_voucher and extra_charge

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fee_voucher", sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("fee_voucher", sa.Column("discount_reason", sa.String(255), nullable=True))
    op.add_column("extra_charge", sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("extra_charge", sa.Column("discount_reason", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("extra_charge", "discount_reason")
    op.drop_column("extra_charge", "discount_amount")
    op.drop_column("fee_voucher", "discount_reason")
    op.drop_column("fee_voucher", "discount_amount")
