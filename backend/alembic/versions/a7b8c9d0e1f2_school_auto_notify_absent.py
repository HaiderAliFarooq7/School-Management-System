"""school.auto_notify_absent flag (per-school toggle for auto absent push)

Additive: adds a boolean to the school table, default true, so behaviour is
unchanged unless an admin turns it off. Applied to every tenant database via
the existing startup migration path.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-05 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "school",
        sa.Column("auto_notify_absent", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("school", "auto_notify_absent")
