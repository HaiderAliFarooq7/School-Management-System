import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade
from app.models.payment_history import PaymentHistory
from app.models.student import Student
from app.schemas.fee_voucher import (
    BulkDeleteResult,
    BulkDeleteVouchersRequest,
    BulkGenerateRequest,
    BulkPayRequest,
    DiscountRequest,
    GenerateVoucherRequest,
    PayVoucherRequest,
    SelectedVouchersPdfRequest,
    VoucherEditRequest,
    VoucherFilterRow,
    VoucherOut,
    VoucherSearchResult,
    VoucherWithStudentOut,
)
from app.services import audit_service, voucher_pdf
from app.services.class_order import class_sort_key
from app.services.search import fuzzy_pick, looks_like_name, text_search_condition

router = APIRouter(
    prefix="/api/fee-vouchers",
    tags=["fee_vouchers"],
    dependencies=[Depends(require_role("Admin", "Accountant"))],
)
require_admin = Depends(require_role("Admin"))

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def month_label_and_sort(year: int, month: int) -> tuple[str, str]:
    return f"{_MONTHS[month - 1]} {year}", f"{year:04d}-{month:02d}"


def _recompute_status(total_amount: float, paid_amount: float, discount_amount: float = 0) -> str:
    """A voucher counts as Paid once payments + discount cover the total — a
    parent who got Rs. 500 relaxed and paid the rest is fully settled, not
    'partially paid'."""
    if paid_amount <= 0 and discount_amount <= 0:
        return "Unpaid"
    if paid_amount + discount_amount >= total_amount:
        return "Paid"
    return "Partial"


def _is_overdue(fee_month_sort: str, status_value: str, due_day: int) -> bool:
    if status_value == "Paid":
        return False
    today = date.today()
    current_sort = f"{today.year:04d}-{today.month:02d}"
    if fee_month_sort < current_sort:
        return True
    if fee_month_sort == current_sort and today.day > due_day:
        return True
    return False


def _generate_voucher(db: Session, student_id: int, year: int, month: int, total_amount: float) -> FeeVoucher:
    """Create the month's voucher if absent; if it exists, update total_amount
    only and never touch paid_amount/discount, so they survive a regenerate."""
    fee_month, fee_month_sort = month_label_and_sort(year, month)
    existing = db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id == student_id, FeeVoucher.fee_month == fee_month)
    ).scalar_one_or_none()
    if existing:
        existing.total_amount = total_amount
        existing.status = _recompute_status(total_amount, float(existing.paid_amount), float(existing.discount_amount))
        db.commit()
        return existing
    voucher = FeeVoucher(
        student_id=student_id,
        fee_month=fee_month,
        fee_month_sort=fee_month_sort,
        total_amount=total_amount,
        paid_amount=0,
        discount_amount=0,
        status="Unpaid",
    )
    db.add(voucher)
    db.commit()
    return voucher


@router.get("", response_model=list[VoucherWithStudentOut])
def list_vouchers_for_class(class_name: str, status_filter: str = "", db: Session = Depends(get_db)):
    query = (
        select(FeeVoucher, Student.name, Student.registration_no)
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(Student.class_name == class_name)
    )
    if status_filter:
        query = query.where(FeeVoucher.status == status_filter)
    query = query.order_by(FeeVoucher.fee_month_sort)
    rows = db.execute(query).all()
    return [
        VoucherWithStudentOut(
            **VoucherOut.model_validate(v).model_dump(), student_name=name, registration_no=reg
        )
        for v, name, reg in rows
    ]


@router.get("/search", response_model=list[VoucherSearchResult])
def search_vouchers(query: str, db: Session = Depends(get_db)):
    """Find vouchers by voucher number, student name, registration no, phone, or CNIC —
    mirrors how a real fee counter looks a student up from the printed voucher."""
    filters = text_search_condition(
        query, Student.name, Student.registration_no, Student.phone, Student.cnic,
    )
    if query.strip().isdigit():
        filters = filters | (FeeVoucher.voucher_id == int(query.strip()))
    # Typo-tolerant: also pull vouchers of students whose name is a close
    # spelling match ("abdulhady" → "Abdul Hadi").
    if looks_like_name(query):
        pairs = db.execute(select(Student.student_id, Student.name)).all()
        fuzzy_ids = fuzzy_pick(query, pairs)
        if fuzzy_ids:
            filters = filters | Student.student_id.in_(fuzzy_ids)

    rows = db.execute(
        select(FeeVoucher, Student)
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(filters)
        .order_by(FeeVoucher.fee_month_sort.desc())
        .limit(100)
    ).all()

    # Everything each matched student still owes, fetched once for the whole
    # result set (2 queries) instead of 2 queries per row.
    student_ids = list({student.student_id for _, student in rows})
    voucher_pending_by_student: dict[int, float] = {}
    voucher_pending_by_id: dict[int, float] = {}
    if student_ids:
        for vid, sid, total, paid, discount in db.execute(
            select(
                FeeVoucher.voucher_id, FeeVoucher.student_id,
                FeeVoucher.total_amount, FeeVoucher.paid_amount, FeeVoucher.discount_amount,
            ).where(FeeVoucher.student_id.in_(student_ids), FeeVoucher.status != "Paid")
        ).all():
            pending = max(float(total) - float(paid) - float(discount), 0)
            voucher_pending_by_id[vid] = pending
            voucher_pending_by_student[sid] = voucher_pending_by_student.get(sid, 0) + pending
    charges_pending_by_student = dict(
        db.execute(
            select(ExtraCharge.student_id, func.coalesce(func.sum(ExtraCharge.remaining_amount), 0))
            .where(ExtraCharge.student_id.in_(student_ids), ExtraCharge.status != "Paid")
            .group_by(ExtraCharge.student_id)
        ).all()
    ) if student_ids else {}

    results = []
    for voucher, student in rows:
        other_total = (
            voucher_pending_by_student.get(student.student_id, 0)
            - voucher_pending_by_id.get(voucher.voucher_id, 0)
            + float(charges_pending_by_student.get(student.student_id, 0))
        )
        results.append(
            VoucherSearchResult(
                voucher_id=voucher.voucher_id,
                student_id=student.student_id,
                registration_no=student.registration_no,
                name=student.name,
                class_name=student.class_name,
                phone=student.phone,
                cnic=student.cnic,
                fee_month=voucher.fee_month,
                total_amount=float(voucher.total_amount),
                paid_amount=float(voucher.paid_amount),
                discount_amount=float(voucher.discount_amount),
                status=voucher.status,
                other_pending=round(other_total, 2),
            )
        )
    return results


@router.get("/filter", response_model=list[VoucherFilterRow])
def filter_vouchers(
    class_names: str = "",
    status_filter: str = "",
    year: int | None = None,
    month: int | None = None,
    overdue_only: bool = False,
    charges_pending_only: bool = False,
    due_day: int = 10,
    db: Session = Depends(get_db),
):
    """The advanced filter behind the Fee Vouchers page: any combination of
    class (omit for all classes), status, a specific month, overdue-only, and
    'has pending extra charges' — replaces the old single-class browse view."""
    query = (
        select(FeeVoucher, Student.name, Student.registration_no)
        .join(Student, Student.student_id == FeeVoucher.student_id)
    )
    if class_names:
        query = query.where(Student.class_name.in_(class_names.split(",")))
    if status_filter:
        query = query.where(FeeVoucher.status.in_(status_filter.split(",")))
    if year and month:
        _, fee_month_sort = month_label_and_sort(year, month)
        query = query.where(FeeVoucher.fee_month_sort == fee_month_sort)
    query = query.order_by(Student.class_name, Student.name, FeeVoucher.fee_month_sort)
    rows = db.execute(query).all()

    # extra-charge pending totals for every student in the result, in one query
    student_ids = list({v.student_id for v, _, _ in rows})
    charges_by_student = dict(
        db.execute(
            select(ExtraCharge.student_id, func.coalesce(func.sum(ExtraCharge.remaining_amount), 0))
            .where(ExtraCharge.student_id.in_(student_ids), ExtraCharge.status != "Paid")
            .group_by(ExtraCharge.student_id)
        ).all()
    ) if student_ids else {}

    results = []
    for voucher, name, reg in rows:
        charges_pending = float(charges_by_student.get(voucher.student_id, 0))

        is_overdue = _is_overdue(voucher.fee_month_sort, voucher.status, due_day)
        if overdue_only and not is_overdue:
            continue
        if charges_pending_only and charges_pending <= 0:
            continue

        results.append(
            VoucherFilterRow(
                **VoucherOut.model_validate(voucher).model_dump(),
                student_name=name,
                registration_no=reg,
                is_overdue=is_overdue,
                charges_pending=round(charges_pending, 2),
            )
        )
    return results


@router.post("/bulk-delete", response_model=BulkDeleteResult, dependencies=[require_admin])
def bulk_delete_vouchers(
    payload: BulkDeleteVouchersRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: delete a hand-picked set of vouchers outright — e.g. every
    voucher selected in the filtered grid for a given month — even ones that
    already have a payment or discount recorded."""
    vouchers = db.execute(
        select(FeeVoucher).where(FeeVoucher.voucher_id.in_(payload.voucher_ids))
    ).scalars().all()
    found_ids = {v.voucher_id for v in vouchers}
    skipped = [{"voucher_id": vid, "reason": "Voucher not found"} for vid in payload.voucher_ids if vid not in found_ids]
    for voucher in vouchers:
        audit_service.record(
            db, current_user, action="delete", target_type="fee_voucher", target_id=voucher.voucher_id,
            student=db.get(Student, voucher.student_id), label=voucher.fee_month,
            note=f"total={voucher.total_amount}, paid={voucher.paid_amount}, discount={voucher.discount_amount}",
        )
        # Void this voucher's payments so they leave the collections totals.
        audit_service.void_for_target(
            db, target_type="fee_voucher", target_id=voucher.voucher_id,
            student_id=voucher.student_id, label=voucher.fee_month,
        )
        db.delete(voucher)
    db.commit()
    return BulkDeleteResult(deleted=len(vouchers), skipped=skipped)


@router.get("/{voucher_id}", response_model=VoucherOut)
def get_voucher(voucher_id: int, db: Session = Depends(get_db)):
    voucher = db.get(FeeVoucher, voucher_id)
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    return voucher


@router.post("/generate", response_model=VoucherOut)
def generate_voucher(payload: GenerateVoucherRequest, db: Session = Depends(get_db)):
    return _generate_voucher(db, payload.student_id, payload.year, payload.month, payload.total_amount)


@router.post("/bulk-generate", response_model=list[VoucherOut])
def bulk_generate(payload: BulkGenerateRequest, db: Session = Depends(get_db)):
    """Generate one voucher per active student in the selected classes.
    Each student's own default_fee (set at admission) is used when present;
    otherwise the class's default fee_amount is used."""
    grades = {
        g.class_name: float(g.fee_amount)
        for g in db.execute(select(Grade).where(Grade.class_name.in_(payload.class_names))).scalars().all()
    }
    students = db.execute(
        select(Student).where(Student.class_name.in_(payload.class_names), Student.status == "Active")
    ).scalars().all()
    if not students:
        return []

    # One lookup for every existing voucher this month and one commit for the
    # whole batch, instead of a SELECT + COMMIT per student.
    fee_month, fee_month_sort = month_label_and_sort(payload.year, payload.month)
    existing_by_student = {
        v.student_id: v
        for v in db.execute(
            select(FeeVoucher).where(
                FeeVoucher.student_id.in_([s.student_id for s in students]),
                FeeVoucher.fee_month == fee_month,
            )
        ).scalars().all()
    }
    results = []
    for s in students:
        total = float(s.default_fee) if s.default_fee is not None else grades.get(s.class_name, 0)
        voucher = existing_by_student.get(s.student_id)
        if voucher:
            # Same regenerate rule as _generate_voucher: update the total,
            # never touch paid_amount/discount.
            voucher.total_amount = total
            voucher.status = _recompute_status(total, float(voucher.paid_amount), float(voucher.discount_amount))
        else:
            voucher = FeeVoucher(
                student_id=s.student_id,
                fee_month=fee_month,
                fee_month_sort=fee_month_sort,
                total_amount=total,
                paid_amount=0,
                discount_amount=0,
                status="Unpaid",
            )
            db.add(voucher)
        results.append(voucher)
    db.commit()
    return results


@router.post("/{voucher_id}/pay", response_model=VoucherOut)
def pay_voucher(
    voucher_id: int, payload: PayVoucherRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment amount must be greater than zero.")
    # Row lock so two clerks recording a payment for the same voucher at the
    # same moment can't both pass the balance check and overshoot the total.
    voucher = db.execute(
        select(FeeVoucher).where(FeeVoucher.voucher_id == voucher_id).with_for_update()
    ).scalar_one_or_none()
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    remaining = float(voucher.total_amount) - float(voucher.paid_amount) - float(voucher.discount_amount)
    if payload.amount > remaining + 1e-6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Payment exceeds remaining balance of {remaining:.2f}.")
    voucher.paid_amount = float(voucher.paid_amount) + payload.amount
    voucher.status = _recompute_status(float(voucher.total_amount), float(voucher.paid_amount), float(voucher.discount_amount))
    db.add(PaymentHistory(target_type="fee_voucher", target_id=voucher_id, amount=payload.amount, paid_at=datetime.now()))
    audit_service.record(
        db, current_user, action="payment", target_type="fee_voucher", target_id=voucher_id,
        student=db.get(Student, voucher.student_id), label=voucher.fee_month, amount=payload.amount,
    )
    db.commit()
    return voucher


@router.post("/{voucher_id}/discount", response_model=VoucherOut, dependencies=[require_admin])
def apply_discount(
    voucher_id: int, payload: DiscountRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Apply a fee concession/relaxation (e.g. a parent asks for Rs. 500 off).
    The discount plus whatever's already been paid settle the voucher —
    a partially-paid voucher can become fully 'Paid' once the discount covers
    the rest, with no further cash payment needed."""
    if payload.amount < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Discount amount cannot be negative.")
    voucher = db.get(FeeVoucher, voucher_id)
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    max_discount = float(voucher.total_amount) - float(voucher.paid_amount)
    if payload.amount > max_discount + 1e-6:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Discount cannot exceed the unpaid balance of {max_discount:.2f}.",
        )
    voucher.discount_amount = payload.amount
    voucher.discount_reason = payload.reason or None
    voucher.status = _recompute_status(float(voucher.total_amount), float(voucher.paid_amount), payload.amount)
    audit_service.record(
        db, current_user, action="discount", target_type="fee_voucher", target_id=voucher_id,
        student=db.get(Student, voucher.student_id), label=voucher.fee_month,
        amount=payload.amount, reason=payload.reason,
    )
    db.commit()
    return voucher


@router.post("/bulk-pay", response_model=list[VoucherOut])
def bulk_pay(
    payload: BulkPayRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _, fee_month_sort = month_label_and_sort(payload.year, payload.month)
    vouchers = db.execute(
        select(FeeVoucher)
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(Student.class_name == payload.class_name, FeeVoucher.fee_month_sort == fee_month_sort)
    ).scalars().all()
    results = []
    for voucher in vouchers:
        remaining = float(voucher.total_amount) - float(voucher.paid_amount) - float(voucher.discount_amount)
        amount = min(payload.amount_per_student, remaining)
        if amount <= 0:
            results.append(voucher)
            continue
        voucher.paid_amount = float(voucher.paid_amount) + amount
        voucher.status = _recompute_status(float(voucher.total_amount), float(voucher.paid_amount), float(voucher.discount_amount))
        db.add(PaymentHistory(target_type="fee_voucher", target_id=voucher.voucher_id, amount=amount, paid_at=datetime.now()))
        audit_service.record(
            db, current_user, action="payment", target_type="fee_voucher", target_id=voucher.voucher_id,
            student=db.get(Student, voucher.student_id), label=voucher.fee_month, amount=amount,
            note="bulk pay",
        )
        results.append(voucher)
    db.commit()
    return results


@router.get("/{voucher_id}/pdf")
def get_voucher_pdf(voucher_id: int, db: Session = Depends(get_db)):
    voucher = db.get(FeeVoucher, voucher_id)
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    student = db.get(Student, voucher.student_id)
    buffer = io.BytesIO()
    voucher_pdf.generate_single_voucher_pdf(db, student, voucher, buffer)
    buffer.seek(0)
    filename = f"{student.registration_no}_{voucher.fee_month.replace(' ', '_')}.pdf"
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/pdf/selected")
def get_selected_vouchers_pdf(payload: SelectedVouchersPdfRequest, db: Session = Depends(get_db)):
    """Generates one combined PDF for a hand-picked list of vouchers — covers both
    'class-wise' (pass every voucher in a class) and 'selected students' use cases."""
    vouchers = db.execute(select(FeeVoucher).where(FeeVoucher.voucher_id.in_(payload.voucher_ids))).scalars().all()
    if not vouchers:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No matching vouchers found")
    students = {s.student_id: s for s in db.execute(
        select(Student).where(Student.student_id.in_([v.student_id for v in vouchers]))
    ).scalars().all()}
    pairs = [(students[v.student_id], v) for v in vouchers if v.student_id in students]

    buffer = io.BytesIO()
    if payload.mode == "individual":
        voucher_pdf.generate_individual_pages_pdf(db, pairs, buffer)
    else:
        voucher_pdf.generate_4_per_sheet_pdf(db, pairs, buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=fee_vouchers.pdf"},
    )


@router.get("/pdf/class")
def get_class_vouchers_pdf(class_name: str, year: int, month: int, mode: str = "4up", db: Session = Depends(get_db)):
    """One combined PDF for every voucher in a class for the given month —
    the typical 'print vouchers for the whole class' workflow."""
    _, fee_month_sort = month_label_and_sort(year, month)
    rows = db.execute(
        select(FeeVoucher, Student)
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(Student.class_name == class_name, FeeVoucher.fee_month_sort == fee_month_sort)
        .order_by(Student.name)
    ).all()
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No vouchers found for this class/month — generate them first.")
    pairs = [(student, voucher) for voucher, student in rows]

    buffer = io.BytesIO()
    if mode == "individual":
        voucher_pdf.generate_individual_pages_pdf(db, pairs, buffer)
    else:
        voucher_pdf.generate_4_per_sheet_pdf(db, pairs, buffer)
    buffer.seek(0)
    filename = f"{class_name.replace(' ', '_')}_{year}_{month:02d}.pdf"
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf/all-students")
def get_all_students_vouchers_pdf(
    class_names: str = "", mode: str = "4up", note: str = "", db: Session = Depends(get_db),
):
    """One combined PDF with every active student's COMPLETE pending dues —
    every unpaid/partial month plus every open extra charge, rolled into a
    single challan per student with a Grand Total row — across every class
    unless class_names restricts it. Students with nothing outstanding are
    skipped. 4-per-sheet by default."""
    query = select(Student).where(Student.status == "Active")
    if class_names:
        query = query.where(Student.class_name.in_(class_names.split(",")))
    students = db.execute(query).scalars().all()
    if not students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active students found.")
    # Class-wise order (Playgroup → Grade 10), then by student name within a class,
    # so the printed challans come out sorted the way the office files them.
    students = sorted(students, key=lambda s: (class_sort_key(s.class_name), (s.name or "").lower()))

    buffer = io.BytesIO()
    try:
        if mode == "individual":
            voucher_pdf.generate_all_dues_individual_pdf(db, students, buffer, note=note or None)
        else:
            voucher_pdf.generate_all_dues_4_per_sheet_pdf(db, students, buffer, note=note or None)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=all_challans.pdf"},
    )


@router.get("/pdf/student/{student_id}")
def get_single_student_dues_pdf(student_id: int, note: str = "", db: Session = Depends(get_db)):
    """One student's complete pending dues, laid out 4-up on a single A4
    sheet (one filled quadrant, three left blank) — printing a lone challan
    on a full page wastes 3/4 of the sheet, so this always uses the 4-up
    layout, the same as the multi-student challan run."""
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    buffer = io.BytesIO()
    try:
        voucher_pdf.generate_all_dues_4_per_sheet_pdf(db, [student], buffer, note=note or None)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    buffer.seek(0)
    filename = f"{student.registration_no}_challan.pdf"
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf/students")
def get_students_dues_pdf(student_ids: str, note: str = "", db: Session = Depends(get_db)):
    """Complete pending dues for an explicit list of students (e.g. a
    student plus their siblings), 4-up on as many A4 sheets as needed —
    the last sheet leaves blank quadrants rather than wasting a full page
    per student. Students with nothing outstanding are skipped."""
    try:
        ids = [int(x) for x in student_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "student_ids must be a comma-separated list of numbers")
    if not ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No student ids given")
    students = db.execute(select(Student).where(Student.student_id.in_(ids))).scalars().all()
    if not students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No matching students found")
    order = {sid: i for i, sid in enumerate(ids)}
    students = sorted(students, key=lambda s: order.get(s.student_id, 0))

    buffer = io.BytesIO()
    try:
        voucher_pdf.generate_all_dues_4_per_sheet_pdf(db, students, buffer, note=note or None)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=challans.pdf"},
    )


@router.delete("/{voucher_id}", dependencies=[require_admin])
def delete_voucher(
    voucher_id: int, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: delete any voucher outright, even one with payments or a
    discount already recorded — Accountants can never delete a voucher."""
    voucher = db.get(FeeVoucher, voucher_id)
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    audit_service.record(
        db, current_user, action="delete", target_type="fee_voucher", target_id=voucher_id,
        student=db.get(Student, voucher.student_id), label=voucher.fee_month,
        note=f"total={voucher.total_amount}, paid={voucher.paid_amount}, discount={voucher.discount_amount}",
    )
    # The voucher's payments no longer correspond to anything — void them so
    # they drop out of the accountant's collections total.
    audit_service.void_for_target(
        db, target_type="fee_voucher", target_id=voucher_id,
        student_id=voucher.student_id, label=voucher.fee_month,
    )
    db.delete(voucher)
    db.commit()
    return {"detail": "Deleted"}


@router.put("/{voucher_id}", response_model=VoucherOut, dependencies=[require_admin])
def edit_voucher(
    voucher_id: int, payload: VoucherEditRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: directly overwrite a voucher's figures, including ones that
    are already fully paid — fixes data-entry mistakes without having to
    delete and recreate the voucher."""
    voucher = db.get(FeeVoucher, voucher_id)
    if voucher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voucher not found")
    voucher.total_amount = payload.total_amount
    voucher.paid_amount = payload.paid_amount
    voucher.discount_amount = payload.discount_amount
    voucher.discount_reason = payload.discount_reason
    voucher.status = _recompute_status(payload.total_amount, payload.paid_amount, payload.discount_amount)
    audit_service.record(
        db, current_user, action="edit", target_type="fee_voucher", target_id=voucher_id,
        student=db.get(Student, voucher.student_id), label=voucher.fee_month,
        amount=payload.total_amount, reason=payload.discount_reason,
        note=f"total={payload.total_amount}, paid={payload.paid_amount}, discount={payload.discount_amount}",
    )
    db.commit()
    return voucher
