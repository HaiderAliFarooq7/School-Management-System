"""store school logo in the database

The uploaded logo used to be written to DATA_DIR on disk. On Render that
directory is ephemeral — wiped on every restart, redeploy, or free-tier idle
spin-down — so uploaded logos silently disappeared in production. The logo
bytes now live in the school row (Neon is the only durable storage in this
deployment); logo_path is kept as a legacy fallback that bootstrap imports
into logo_data at startup when the file still exists.

Revision ID: e5f6a7b8c9d0
Revises: c3d4e5f6a7b8
Create Date: 2026-07-03 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e5f6a7b8c9d0'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('school', sa.Column('logo_data', sa.LargeBinary(), nullable=True))
    op.add_column('school', sa.Column('logo_mime', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('school', 'logo_mime')
    op.drop_column('school', 'logo_data')
