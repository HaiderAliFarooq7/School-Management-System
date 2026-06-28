"""whatsapp cloud provider

Revision ID: 332902abaa38
Revises: 51c86d7c98c5
Create Date: 2026-06-28 00:50:39.676008

"""
from alembic import op
import sqlalchemy as sa

revision = '332902abaa38'
down_revision = '51c86d7c98c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('communication_provider', sa.Column('business_name', sa.String(length=255), nullable=True))
    op.add_column('communication_provider', sa.Column('phone_number_display', sa.String(length=50), nullable=True))
    op.add_column('communication_provider', sa.Column('api_version', sa.String(length=20), nullable=True))
    op.add_column('communication_provider', sa.Column('last_tested_at', sa.DateTime(), nullable=True))
    op.add_column('communication_provider', sa.Column('last_test_status', sa.String(length=20), nullable=True))
    op.add_column('communication_provider', sa.Column('last_error', sa.String(), nullable=True))

    op.add_column('notification_log', sa.Column('template', sa.String(length=150), nullable=True))
    op.add_column('notification_log', sa.Column('meta_message_id', sa.String(length=100), nullable=True))
    op.add_column('notification_log', sa.Column('http_status', sa.Integer(), nullable=True))
    op.alter_column('notification_log', 'student_id', existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint(op.f('notification_log_student_id_fkey'), 'notification_log', type_='foreignkey')
    op.create_foreign_key(
        'notification_log_student_id_fkey', 'notification_log', 'student',
        ['student_id'], ['student_id'], ondelete='SET NULL',
    )

    op.add_column('notification_template', sa.Column('whatsapp_template_name', sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column('notification_template', 'whatsapp_template_name')

    op.drop_constraint('notification_log_student_id_fkey', 'notification_log', type_='foreignkey')
    op.create_foreign_key(
        'notification_log_student_id_fkey', 'notification_log', 'student',
        ['student_id'], ['student_id'], ondelete='CASCADE',
    )
    op.alter_column('notification_log', 'student_id', existing_type=sa.INTEGER(), nullable=False)
    op.drop_column('notification_log', 'http_status')
    op.drop_column('notification_log', 'meta_message_id')
    op.drop_column('notification_log', 'template')

    op.drop_column('communication_provider', 'last_error')
    op.drop_column('communication_provider', 'last_test_status')
    op.drop_column('communication_provider', 'last_tested_at')
    op.drop_column('communication_provider', 'api_version')
    op.drop_column('communication_provider', 'phone_number_display')
    op.drop_column('communication_provider', 'business_name')
