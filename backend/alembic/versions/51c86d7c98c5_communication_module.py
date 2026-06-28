"""communication module

Revision ID: 51c86d7c98c5
Revises: 0004
Create Date: 2026-06-27 20:09:53.366169

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '51c86d7c98c5'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('communication_provider',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('configuration_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('notification_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table('notification_queue',
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
    op.add_column('notification_log', sa.Column('provider', sa.String(length=50), nullable=True))
    op.add_column('notification_log', sa.Column('recipient', sa.String(length=255), nullable=True))
    op.add_column('notification_log', sa.Column('attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('notification_log', sa.Column('response', sa.String(), nullable=True))
    op.add_column('notification_log', sa.Column('error', sa.String(), nullable=True))
    op.add_column('notification_log', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('school', sa.Column('auto_notify_absent', sa.Boolean(), server_default=sa.false(), nullable=False))

    op.execute("""
        INSERT INTO notification_template (name, type, message, variables, enabled) VALUES
        ('Attendance Absent', 'attendance_absent',
         '{{student_name}} was marked ABSENT on {{date}} for class {{class}}. - {{school_name}}',
         '["student_name","parent_name","class","date","school_name"]'::jsonb, true),
        ('Pending Fee', 'fee_reminder',
         'Dear {{parent_name}}, {{student_name}} ({{class}}) has a pending fee balance of Rs. {{remaining_fee}}. Voucher: {{voucher_no}}. - {{school_name}}',
         '["student_name","parent_name","class","remaining_fee","voucher_no","school_name"]'::jsonb, true),
        ('Custom Message', 'custom', '', '["student_name","parent_name","class","date","school_name"]'::jsonb, true)
    """)
    op.execute("""
        INSERT INTO communication_provider (name, type, enabled, configuration_json) VALUES
        ('Android SMS Gateway', 'android_gateway', false, '{}'::jsonb),
        ('WhatsApp Cloud API', 'whatsapp_cloud', false, '{}'::jsonb)
    """)


def downgrade() -> None:
    op.drop_column('school', 'auto_notify_absent')
    op.drop_column('notification_log', 'updated_at')
    op.drop_column('notification_log', 'error')
    op.drop_column('notification_log', 'response')
    op.drop_column('notification_log', 'attempts')
    op.drop_column('notification_log', 'recipient')
    op.drop_column('notification_log', 'provider')
    op.drop_table('notification_queue')
    op.drop_table('notification_template')
    op.drop_table('communication_provider')
