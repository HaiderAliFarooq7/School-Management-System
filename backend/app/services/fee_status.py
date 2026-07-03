from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher


def aggregate_fee_status(vouchers: list[FeeVoucher]) -> str:
    """A student's overall fee status across all their vouchers. Partial only
    applies when exactly one month's fee is outstanding and it has been paid
    against — any other mix of unpaid/partial months (more than one
    outstanding month) counts as Unpaid, since a parent who's behind on two
    or more months hasn't earned the softer 'Partial' label."""
    if not vouchers:
        return "No Vouchers"
    pending = [v for v in vouchers if v.status != "Paid"]
    if not pending:
        return "Paid"
    if len(pending) > 1:
        return "Unpaid"
    return "Partial" if float(pending[0].paid_amount) > 0 else "Unpaid"


def fee_summaries_for_students(db: Session, student_ids: list[int]) -> dict[int, tuple[str, float]]:
    """(fee_status, total_pending) for every requested student in exactly two
    queries, however many students are asked for — replaces the previous
    3-queries-per-student pattern that made the student list O(N) round trips."""
    if not student_ids:
        return {}

    vouchers_by_student: dict[int, list[FeeVoucher]] = defaultdict(list)
    for v in db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id.in_(student_ids))
    ).scalars():
        vouchers_by_student[v.student_id].append(v)

    charges_pending = dict(
        db.execute(
            select(ExtraCharge.student_id, func.coalesce(func.sum(ExtraCharge.remaining_amount), 0))
            .where(ExtraCharge.student_id.in_(student_ids), ExtraCharge.status != "Paid")
            .group_by(ExtraCharge.student_id)
        ).all()
    )

    summaries: dict[int, tuple[str, float]] = {}
    for sid in student_ids:
        vouchers = vouchers_by_student.get(sid, [])
        voucher_pending = sum(
            max(float(v.total_amount) - float(v.paid_amount) - float(v.discount_amount), 0)
            for v in vouchers
        )
        total_pending = round(voucher_pending + float(charges_pending.get(sid, 0)), 2)
        summaries[sid] = (aggregate_fee_status(vouchers), total_pending)
    return summaries
