"""add challan_note to school

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("school", sa.Column("challan_note", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("school", "challan_note")
