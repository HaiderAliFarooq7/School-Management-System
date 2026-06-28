import datetime
import io

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_role
from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade
from app.models.student import Student
from app.services import report_pdf
from app.services.fee_status import aggregate_fee_status

router = APIRouter(
    prefix="/api/fee-reports",
    tags=["fee_reports"],
    dependencies=[Depends(require_role("Admin", "Accountant"))],
)
require_admin = Depends(require_role("Admin"))

PENDING_REPORT_COLUMNS = {
    "registration_no": "Reg No",
    "name": "Name",
    "father_name": "Father's Name",
    "class_name": "Class",
    "phone": "Phone",
    "cnic": "CNIC",
    "vouchers_pending": "Fee Pending (Rs.)",
    "charges_pending": "Charges Pending (Rs.)",
    "total_pending": "Total Pending (Rs.)",
    "fee_status": "Fee Status",
}
DEFAULT_PENDING_COLUMNS = [
    "registration_no", "name", "father_name", "class_name", "total_pending", "fee_status",
]


def _gather_pending_report(db: Session, class_names: str, status_filter: str, due_day: int) -> list[dict]:
    """One row per active student: name/class/father's name plus pending fee
    collected across every unpaid/partial month and every open extra charge —
    sorted class ascending, then name ascending, exactly as printed rosters expect."""
    query = select(Student).where(Student.status == "Active")
    if class_names:
        query = query.where(Student.class_name.in_(class_names.split(",")))
    query = query.order_by(Student.class_name, Student.name)
    students = db.execute(query).scalars().all()

    today = datetime.date.today()
    current_sort = f"{today.year:04d}-{today.month:02d}"
    rows = []
    for s in students:
        vouchers = db.execute(select(FeeVoucher).where(FeeVoucher.student_id == s.student_id)).scalars().all()
        charges = db.execute(
            select(ExtraCharge).where(ExtraCharge.student_id == s.student_id, ExtraCharge.status != "Paid")
        ).scalars().all()

        vouchers_pending = sum(
            max(float(v.total_amount) - float(v.paid_amount) - float(v.discount_amount), 0) for v in vouchers
        )
        charges_pending = sum(float(c.remaining_amount) for c in charges)
        total_pending = round(vouchers_pending + charges_pending, 2)

        fee_status = aggregate_fee_status(vouchers)

        is_overdue = False
        for v in vouchers:
            if v.status == "Paid":
                continue
            if v.fee_month_sort < current_sort:
                is_overdue = True
                break
            if v.fee_month_sort == current_sort and today.day > due_day:
                is_overdue = True
                break

        if status_filter == "Overdue" and not is_overdue:
            continue
        if status_filter and status_filter != "Overdue" and fee_status != status_filter:
            continue

        rows.append({
            "student_id": s.student_id,
            "registration_no": s.registration_no,
            "name": s.name,
            "father_name": s.father_name,
            "class_name": s.class_name,
            "phone": s.phone,
            "cnic": s.cnic,
            "vouchers_pending": round(vouchers_pending, 2),
            "charges_pending": round(charges_pending, 2),
            "total_pending": total_pending,
            "fee_status": fee_status,
            "is_overdue": is_overdue,
        })
    return rows


@router.get("/pending")
def get_pending_report(
    class_names: str = "",
    status_filter: str = "",
    due_day: int = 10,
    db: Session = Depends(get_db),
):
    """Per-student pending-fee report — filter by class (omit for all) and by
    Due/Partial/Unpaid/Overdue/Paid/No Vouchers status."""
    return _gather_pending_report(db, class_names, status_filter, due_day)


@router.get("/pending/pdf")
def get_pending_report_pdf(
    class_names: str = "",
    status_filter: str = "",
    due_day: int = 10,
    columns: str = "",
    db: Session = Depends(get_db),
):
    """Same data as /pending, rendered as a PDF table — sorted class-wise then
    by name. Pick which columns to include via ?columns=registration_no,name,..."""
    selected_columns = [c for c in columns.split(",") if c in PENDING_REPORT_COLUMNS] if columns else DEFAULT_PENDING_COLUMNS
    if not selected_columns:
        selected_columns = DEFAULT_PENDING_COLUMNS

    rows = _gather_pending_report(db, class_names, status_filter, due_day)
    headers = [PENDING_REPORT_COLUMNS[c] for c in selected_columns]
    table_rows = [[str(row.get(c, "") if row.get(c) is not None else "") for c in selected_columns] for row in rows]

    buffer = io.BytesIO()
    report_pdf.generate_table_report_pdf(db, buffer, "Pending Fee Report", headers, table_rows)
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=pending_fee_report.pdf"},
    )


@router.get("/pending/xlsx")
def get_pending_report_xlsx(
    class_names: str = "",
    status_filter: str = "",
    due_day: int = 10,
    columns: str = "",
    db: Session = Depends(get_db),
):
    """Same data as /pending, rendered as an Excel workbook with the same
    selected columns as the PDF export."""
    selected_columns = [c for c in columns.split(",") if c in PENDING_REPORT_COLUMNS] if columns else DEFAULT_PENDING_COLUMNS
    if not selected_columns:
        selected_columns = DEFAULT_PENDING_COLUMNS

    rows = _gather_pending_report(db, class_names, status_filter, due_day)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pending Fee Report"
    ws.append([PENDING_REPORT_COLUMNS[c] for c in selected_columns])
    for row in rows:
        ws.append([row.get(c) for c in selected_columns])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=pending_fee_report.xlsx"},
    )


@router.get("/monthly-collection")
def get_monthly_collection(year: int, month: int, class_name: str = "", db: Session = Depends(get_db)):
    fee_month_sort = f"{year:04d}-{month:02d}"

    class_query = (
        select(
            Grade.class_name,
            func.count(func.distinct(Student.student_id)),
            func.coalesce(func.sum(FeeVoucher.total_amount), 0),
            func.coalesce(func.sum(FeeVoucher.paid_amount), 0),
            func.coalesce(func.sum(FeeVoucher.discount_amount), 0),
        )
        .outerjoin(Student, (Student.class_name == Grade.class_name) & (Student.status == "Active"))
        .outerjoin(
            FeeVoucher,
            (FeeVoucher.student_id == Student.student_id) & (FeeVoucher.fee_month_sort == fee_month_sort),
        )
    )
    if class_name:
        class_query = class_query.where(Grade.class_name == class_name)
    class_query = class_query.group_by(Grade.class_name).order_by(Grade.class_name)
    rows = db.execute(class_query).all()

    classes = []
    grand_total = grand_collected = grand_discounted = 0.0
    for cname, student_count, total, collected, discounted in rows:
        total = float(total)
        collected = float(collected)
        discounted = float(discounted)
        classes.append({
            "class_name": cname,
            "student_count": student_count,
            "total": total,
            "collected": collected,
            "discounted": discounted,
            "pending": max(total - collected - discounted, 0),
            "pct": ((collected + discounted) / total * 100) if total > 0 else 0,
        })
        grand_total += total
        grand_collected += collected
        grand_discounted += discounted

    detail_query = (
        select(
            Student.registration_no, Student.name, Student.class_name,
            FeeVoucher.total_amount, FeeVoucher.paid_amount, FeeVoucher.discount_amount, FeeVoucher.status,
        )
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(FeeVoucher.fee_month_sort == fee_month_sort)
    )
    if class_name:
        detail_query = detail_query.where(Student.class_name == class_name)
    detail_query = detail_query.order_by(Student.class_name, Student.name)
    details = db.execute(detail_query).all()

    return {
        "year": year,
        "month": month,
        "classes": classes,
        "grand_total": grand_total,
        "grand_collected": grand_collected,
        "grand_discounted": grand_discounted,
        "grand_pending": max(grand_total - grand_collected - grand_discounted, 0),
        "details": [
            {
                "registration_no": r[0], "name": r[1], "class_name": r[2],
                "total_amount": float(r[3]), "paid_amount": float(r[4]), "discount_amount": float(r[5]), "status": r[6],
            }
            for r in details
        ],
    }


@router.get("/class-summary")
def get_class_fee_summary(class_name: str, year: int, month: int, db: Session = Depends(get_db)):
    fee_month_sort = f"{year:04d}-{month:02d}"
    rows = db.execute(
        select(FeeVoucher.total_amount, FeeVoucher.paid_amount, FeeVoucher.discount_amount, FeeVoucher.status)
        .join(Student, Student.student_id == FeeVoucher.student_id)
        .where(Student.class_name == class_name, FeeVoucher.fee_month_sort == fee_month_sort)
    ).all()
    total_students = len(rows)
    total_fee = sum(float(r[0]) for r in rows)
    total_collected = sum(float(r[1]) for r in rows)
    total_discounted = sum(float(r[2]) for r in rows)
    paid_count = sum(1 for r in rows if r[3] == "Paid")
    partial_rows = [r for r in rows if r[3] == "Partial"]
    unpaid_count = sum(1 for r in rows if r[3] == "Unpaid")
    avg_partial_pending = (
        sum(float(r[0]) - float(r[1]) - float(r[2]) for r in partial_rows) / len(partial_rows) if partial_rows else 0
    )
    return {
        "class_name": class_name,
        "year": year,
        "month": month,
        "total_students": total_students,
        "total_fee": total_fee,
        "total_collected": total_collected,
        "total_discounted": total_discounted,
        "total_pending": max(total_fee - total_collected - total_discounted, 0),
        "paid_count": paid_count,
        "partial_count": len(partial_rows),
        "unpaid_count": unpaid_count,
        "avg_partial_pending": avg_partial_pending,
    }


@router.get("/balance-sheet/{student_id}")
def get_student_balance_sheet(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    vouchers = db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id == student_id).order_by(FeeVoucher.fee_month_sort.desc())
    ).scalars().all()
    charges = db.execute(
        select(ExtraCharge).where(ExtraCharge.student_id == student_id).order_by(ExtraCharge.created_at.desc())
    ).scalars().all()
    total_fees_due = sum(float(v.total_amount) for v in vouchers) + sum(float(c.amount) for c in charges)
    total_paid = sum(float(v.paid_amount) for v in vouchers) + sum(float(c.paid_amount) for c in charges)
    total_discounted = sum(float(v.discount_amount) for v in vouchers) + sum(float(c.discount_amount) for c in charges)
    return {
        "student": {
            "student_id": student.student_id,
            "registration_no": student.registration_no,
            "name": student.name,
            "class_name": student.class_name,
        },
        "vouchers": [
            {"voucher_id": v.voucher_id, "fee_month": v.fee_month, "total_amount": float(v.total_amount),
             "paid_amount": float(v.paid_amount), "discount_amount": float(v.discount_amount),
             "discount_reason": v.discount_reason, "status": v.status}
            for v in vouchers
        ],
        "charges": [
            {"charge_id": c.charge_id, "description": c.description, "amount": float(c.amount),
             "paid_amount": float(c.paid_amount), "discount_amount": float(c.discount_amount),
             "discount_reason": c.discount_reason, "status": c.status}
            for c in charges
        ],
        "total_fees_due": total_fees_due,
        "total_paid": total_paid,
        "total_discounted": total_discounted,
        "total_pending": max(total_fees_due - total_paid - total_discounted, 0),
    }


@router.get("/analytics", dependencies=[require_admin])
def get_fee_analytics(months: int = 6, class_name: str = "", db: Session = Depends(get_db)):
    """Admin-only: the complete school fee/charges picture — totals, a
    per-class breakdown, a month-by-month collection trend, and voucher
    status counts — with an optional class filter."""
    voucher_query = select(FeeVoucher).join(Student, Student.student_id == FeeVoucher.student_id)
    if class_name:
        voucher_query = voucher_query.where(Student.class_name == class_name)
    vouchers = db.execute(voucher_query).scalars().all()

    total_billed = sum(float(v.total_amount) for v in vouchers)
    total_collected = sum(float(v.paid_amount) for v in vouchers)
    total_discounted = sum(float(v.discount_amount) for v in vouchers)
    total_outstanding = max(total_billed - total_collected - total_discounted, 0)
    status_counts = {"Paid": 0, "Partial": 0, "Unpaid": 0}
    for v in vouchers:
        status_counts[v.status] = status_counts.get(v.status, 0) + 1

    charge_query = select(ExtraCharge)
    if class_name:
        charge_query = charge_query.join(Student, Student.student_id == ExtraCharge.student_id).where(
            Student.class_name == class_name
        )
    charges = db.execute(charge_query).scalars().all()
    charges_total = sum(float(c.amount) for c in charges)
    charges_collected = sum(float(c.paid_amount) for c in charges)
    charges_discounted = sum(float(c.discount_amount) for c in charges)
    charges_pending = sum(float(c.remaining_amount) for c in charges if c.status != "Paid")

    by_class_query = (
        select(
            Grade.class_name,
            func.count(func.distinct(Student.student_id)),
            func.coalesce(func.sum(FeeVoucher.total_amount), 0),
            func.coalesce(func.sum(FeeVoucher.paid_amount), 0),
            func.coalesce(func.sum(FeeVoucher.discount_amount), 0),
        )
        .outerjoin(Student, (Student.class_name == Grade.class_name) & (Student.status == "Active"))
        .outerjoin(FeeVoucher, FeeVoucher.student_id == Student.student_id)
    )
    if class_name:
        by_class_query = by_class_query.where(Grade.class_name == class_name)
    by_class_query = by_class_query.group_by(Grade.class_name).order_by(Grade.class_name)
    by_class = []
    for cname, student_count, total, collected, discounted in db.execute(by_class_query).all():
        total, collected, discounted = float(total), float(collected), float(discounted)
        by_class.append({
            "class_name": cname,
            "student_count": student_count,
            "total": total,
            "collected": collected,
            "discounted": discounted,
            "pending": max(total - collected - discounted, 0),
        })

    today = datetime.date.today()
    monthly_trend = []
    y, m = today.year, today.month
    for _ in range(months):
        sort_key = f"{y:04d}-{m:02d}"
        month_vouchers = [v for v in vouchers if v.fee_month_sort == sort_key]
        monthly_trend.append({
            "month": sort_key,
            "billed": sum(float(v.total_amount) for v in month_vouchers),
            "collected": sum(float(v.paid_amount) for v in month_vouchers),
            "discounted": sum(float(v.discount_amount) for v in month_vouchers),
        })
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    monthly_trend.reverse()

    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_discounted": total_discounted,
        "total_outstanding": total_outstanding,
        "voucher_status_counts": status_counts,
        "charges_total": charges_total,
        "charges_collected": charges_collected,
        "charges_discounted": charges_discounted,
        "charges_pending": charges_pending,
        "by_class": by_class,
        "monthly_trend": monthly_trend,
    }
