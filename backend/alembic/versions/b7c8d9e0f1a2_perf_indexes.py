"""performance indexes

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-28 13:00:00.000000

"""
from alembic import op

revision = 'b7c8d9e0f1a2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_fee_voucher_fee_month_sort', 'fee_voucher', ['fee_month_sort'])
    op.create_index('ix_notification_queue_status_scheduled_at', 'notification_queue', ['status', 'scheduled_at'])


def downgrade() -> None:
    op.drop_index('ix_notification_queue_status_scheduled_at', table_name='notification_queue')
    op.drop_index('ix_fee_voucher_fee_month_sort', table_name='fee_voucher')
