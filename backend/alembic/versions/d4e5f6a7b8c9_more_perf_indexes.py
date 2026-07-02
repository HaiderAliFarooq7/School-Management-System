"""indexes for the hot per-student and per-class lookups

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-02 12:00:00.000000

fee_voucher.student_id and attendance_record.student_id are already covered
by the leading column of their composite unique constraints, so they are not
duplicated here.
"""
from alembic import op

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_extra_charge_student_id', 'extra_charge', ['student_id'])
    op.create_index('ix_extra_charge_status', 'extra_charge', ['status'])
    op.create_index('ix_student_class_name', 'student', ['class_name'])
    op.create_index('ix_student_status', 'student', ['status'])
    op.create_index('ix_fee_voucher_status', 'fee_voucher', ['status'])
    op.create_index('ix_payment_history_target', 'payment_history', ['target_type', 'target_id'])
    op.create_index('ix_attendance_class_date', 'attendance_record', ['class_name', 'attendance_date'])


def downgrade() -> None:
    op.drop_index('ix_attendance_class_date', table_name='attendance_record')
    op.drop_index('ix_payment_history_target', table_name='payment_history')
    op.drop_index('ix_fee_voucher_status', table_name='fee_voucher')
    op.drop_index('ix_student_status', table_name='student')
    op.drop_index('ix_student_class_name', table_name='student')
    op.drop_index('ix_extra_charge_status', table_name='extra_charge')
    op.drop_index('ix_extra_charge_student_id', table_name='extra_charge')
