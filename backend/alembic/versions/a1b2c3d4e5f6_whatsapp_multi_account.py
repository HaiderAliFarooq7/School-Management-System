"""whatsapp multi-account

Revision ID: a1b2c3d4e5f6
Revises: 332902abaa38
Create Date: 2026-06-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '332902abaa38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('communication_provider', sa.Column('business_account_id', sa.String(length=64), nullable=True))
    op.add_column('communication_provider', sa.Column('phone_number_id', sa.String(length=64), nullable=True))
    op.add_column('communication_provider', sa.Column('access_token_encrypted', sa.String(), nullable=True))
    op.add_column('communication_provider', sa.Column('graph_version', sa.String(length=20), nullable=True))
    op.add_column('communication_provider', sa.Column('webhook_verify_token_encrypted', sa.String(), nullable=True))
    op.add_column('communication_provider', sa.Column('webhook_secret_encrypted', sa.String(), nullable=True))
    op.add_column('communication_provider', sa.Column('use_templates', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('communication_provider', sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('communication_provider', 'is_default')
    op.drop_column('communication_provider', 'use_templates')
    op.drop_column('communication_provider', 'webhook_secret_encrypted')
    op.drop_column('communication_provider', 'webhook_verify_token_encrypted')
    op.drop_column('communication_provider', 'graph_version')
    op.drop_column('communication_provider', 'access_token_encrypted')
    op.drop_column('communication_provider', 'phone_number_id')
    op.drop_column('communication_provider', 'business_account_id')
