"""fee_audit_log: target_id + voided, and reconcile legacy payment entries

Adds ``target_id`` (which voucher/charge an entry belongs to) and ``voided``
(kept for audit but excluded from collections) to ``fee_audit_log``.

Also a one-time data cleanup: before this change, deleting a voucher/charge
left its payment entries in the log, so an accountant's Collections total kept
counting money for vouchers that no longer exist (and double-counted when a
voucher was deleted and re-created for the same month). We reconcile each
student+label group of payment entries against the surviving voucher/charge's
current paid amount — keeping the newest entries that add up to what's actually
paid and voiding the leftover.

Additive tenant migration; applied to every school DB via the startup path.

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-07-22 12:00:00.000000

"""
from collections import defaultdict

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "d1e2f3a4b5c6"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def _reconcile(bind, target_type: str, paid_lookup: dict[tuple, float]) -> None:
    """Void the payment entries that don't correspond to money still owed on a
    surviving voucher/charge (newest-first cap against current paid_amount)."""
    entries = bind.execute(
        text(
            "SELECT id, student_id, label, amount FROM fee_audit_log "
            "WHERE action = 'payment' AND target_type = :tt AND voided = false "
            "ORDER BY student_id, label, created_at DESC, id DESC"
        ),
        {"tt": target_type},
    ).fetchall()

    groups: dict[tuple, list] = defaultdict(list)
    for entry_id, student_id, label, amount in entries:
        groups[(student_id, label or "")].append((entry_id, float(amount or 0)))

    void_ids: list[int] = []
    for key, items in groups.items():
        paid = paid_lookup.get(key, 0.0)  # 0.0 when the voucher/charge is gone
        running = 0.0
        for entry_id, amt in items:  # newest first
            if running + amt <= paid + 0.01:
                running += amt
            else:
                void_ids.append(entry_id)

    if void_ids:
        bind.execute(
            text("UPDATE fee_audit_log SET voided = true WHERE id = ANY(:ids)"),
            {"ids": void_ids},
        )


def upgrade() -> None:
    op.add_column("fee_audit_log", sa.Column("target_id", sa.Integer(), nullable=True))
    op.add_column(
        "fee_audit_log",
        sa.Column("voided", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_fee_audit_log_target_id", "fee_audit_log", ["target_id"])

    bind = op.get_bind()

    voucher_paid = {
        (sid, month): float(paid or 0)
        for sid, month, paid in bind.execute(
            text("SELECT student_id, fee_month, paid_amount FROM fee_voucher")
        ).fetchall()
    }
    charge_paid = {
        (sid, desc): float(paid or 0)
        for sid, desc, paid in bind.execute(
            text(
                "SELECT student_id, description, COALESCE(SUM(paid_amount), 0) "
                "FROM extra_charge GROUP BY student_id, description"
            )
        ).fetchall()
    }

    _reconcile(bind, "fee_voucher", voucher_paid)
    _reconcile(bind, "extra_charge", charge_paid)


def downgrade() -> None:
    op.drop_index("ix_fee_audit_log_target_id", table_name="fee_audit_log")
    op.drop_column("fee_audit_log", "voided")
    op.drop_column("fee_audit_log", "target_id")
