"""add student.default_fee

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student", sa.Column("default_fee", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("student", "default_fee")
