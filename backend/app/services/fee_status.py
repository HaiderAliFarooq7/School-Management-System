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
