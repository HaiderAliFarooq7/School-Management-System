"""remove notification/communication system

Removes the entire notification/communication module for v1: the
communication_provider, notification_template, and notification_queue
tables, the notification_log table, and the legacy sms/email/auto-notify
columns on school. This is a permanent product decision for v1, not a
rollback-friendly change — downgrade recreates the schema (for migration
history integrity) but the application no longer has any code that uses it.

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-06-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c3d4e5f6a7b8'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('notification_queue')
    op.drop_table('notification_template')
    op.drop_table('communication_provider')
    op.drop_table('notification_log')

    for col in (
        'sms_enabled', 'sms_gateway', 'sms_api_key', 'sms_api_secret', 'sms_sender_id',
        'email_enabled', 'smtp_server', 'smtp_port', 'smtp_email', 'smtp_password',
        'auto_notify_absent',
    ):
        op.drop_column('school', col)


def downgrade() -> None:
    op.add_column('school', sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('school', sa.Column('sms_gateway', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('sms_api_key', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('sms_api_secret', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('sms_sender_id', sa.String(100), nullable=False, server_default=""))
    op.add_column('school', sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('school', sa.Column('smtp_server', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('smtp_port', sa.Integer(), nullable=False, server_default="587"))
    op.add_column('school', sa.Column('smtp_email', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('smtp_password', sa.String(255), nullable=False, server_default=""))
    op.add_column('school', sa.Column('auto_notify_absent', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        'notification_log',
        sa.Column('log_id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('response', sa.String(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('template', sa.String(length=150), nullable=True),
        sa.Column('meta_message_id', sa.String(length=100), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['student.student_id'], ondelete='SET NULL'),
    )
    op.create_index('idx_notification_log_student_id', 'notification_log', ['student_id'])

    op.create_table(
        'communication_provider',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('configuration_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number_display', sa.String(length=50), nullable=True),
        sa.Column('api_version', sa.String(length=20), nullable=True),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('last_test_status', sa.String(length=20), nullable=True),
        sa.Column('last_error', sa.String(), nullable=True),
        sa.Column('business_account_id', sa.String(length=64), nullable=True),
        sa.Column('phone_number_id', sa.String(length=64), nullable=True),
        sa.Column('access_token_encrypted', sa.String(), nullable=True),
        sa.Column('graph_version', sa.String(length=20), nullable=True),
        sa.Column('webhook_verify_token_encrypted', sa.String(), nullable=True),
        sa.Column('webhook_secret_encrypted', sa.String(), nullable=True),
        sa.Column('use_templates', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'notification_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('whatsapp_template_name', sa.String(length=150), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'notification_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('recipient_name', sa.String(length=150), nullable=True),
        sa.Column('provider_type', sa.String(length=30), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('provider_response', sa.String(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.user_id']),
        sa.ForeignKeyConstraint(['student_id'], ['student.student_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_queue_status_scheduled_at', 'notification_queue', ['status', 'scheduled_at'])
