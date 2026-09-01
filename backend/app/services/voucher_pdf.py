import io
import os
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade
from app.models.school import School
from app.models.student import Student
from app.services import qr_service
from app.services.logo_store import logo_content


def _clean_text(text: str) -> str:
    """Collapses newlines/tabs/repeated whitespace so stray control
    characters (e.g. a pasted line break) never render as a missing-glyph
    box in the PDF."""
    return re.sub(r"\s+", " ", text).strip()


def _get_school(db: Session) -> School:
    school = db.execute(select(School).limit(1)).scalar_one_or_none()
    return school or School()


def _get_class_fee(db: Session, class_name: str) -> float:
    grade = db.execute(select(Grade).where(Grade.class_name == class_name)).scalar_one_or_none()
    return float(grade.fee_amount) if grade else 0.0


def _build_dues_data(student: Student, vouchers: list[FeeVoucher], charges: list[ExtraCharge], qr_voucher: FeeVoucher | None, class_fee: float) -> dict:
    """Turns a student's pending vouchers + open extra charges into the
    Month/Charge—Total—Paid—Pending rows printed on the challan, plus grand
    totals and the voucher (if any) whose QR code should be printed.

    'Discount' here is the standing concession baked into the student's own
    monthly fee versus their class's standard fee (e.g. class fee Rs. 2000,
    this student's fee Rs. 1500 -> 25% discount) — not a one-off voucher
    discount_amount, which is a separate, already-itemized adjustment."""
    rows = []
    for v in vouchers:
        pending = max(float(v.total_amount) - float(v.paid_amount) - float(v.discount_amount), 0)
        rows.append((v.fee_month, float(v.total_amount), float(v.paid_amount), pending))
    for ch in charges:
        rows.append((ch.description, float(ch.amount), float(ch.paid_amount), float(ch.remaining_amount)))

    grand_total = sum(r[1] for r in rows)
    grand_paid = sum(r[2] for r in rows)
    grand_pending = sum(r[3] for r in rows)
    monthly_fee = float(student.default_fee) if student.default_fee is not None else (class_fee or (rows[-1][1] if rows else 0))
    discount_pct = ((class_fee - monthly_fee) / class_fee * 100) if class_fee > 0 and monthly_fee < class_fee else 0

    return {
        "rows": rows,
        "grand_total": grand_total,
        "grand_paid": grand_paid,
        "grand_pending": grand_pending,
        "discount_pct": discount_pct,
        "monthly_fee": monthly_fee,
        "qr_voucher": qr_voucher,
    }


def gather_voucher_data(db: Session, student: Student, voucher: FeeVoucher) -> dict:
    """Anchored to one month's voucher: that month plus every earlier
    pending month plus every open extra charge — used when printing from a
    specific voucher (the per-voucher PDF button, class/selected printing)."""
    all_vouchers = db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id == student.student_id)
    ).scalars().all()
    pending_vouchers = [
        v for v in all_vouchers
        if v.voucher_id == voucher.voucher_id or (v.fee_month_sort < voucher.fee_month_sort and v.status != "Paid")
    ]
    pending_vouchers.sort(key=lambda v: v.fee_month_sort)
    charges = db.execute(
        select(ExtraCharge).where(ExtraCharge.student_id == student.student_id, ExtraCharge.status != "Paid")
    ).scalars().all()
    class_fee = _get_class_fee(db, student.class_name)
    return _build_dues_data(student, pending_vouchers, charges, qr_voucher=voucher, class_fee=class_fee)


def gather_student_dues(db: Session, student: Student) -> dict:
    """Every pending month plus every open extra charge for a student,
    regardless of which month they were generated in — the 'complete
    previous pending dues' challan, not anchored to any single voucher."""
    vouchers = db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id == student.student_id, FeeVoucher.status != "Paid")
    ).scalars().all()
    vouchers.sort(key=lambda v: v.fee_month_sort)
    charges = db.execute(
        select(ExtraCharge).where(ExtraCharge.student_id == student.student_id, ExtraCharge.status != "Paid")
    ).scalars().all()
    qr_voucher = vouchers[-1] if vouchers else None
    class_fee = _get_class_fee(db, student.class_name)
    return _build_dues_data(student, vouchers, charges, qr_voucher=qr_voucher, class_fee=class_fee)


def _draw_receipt(c, db: Session, x0, y0, w, h, student: Student, data: dict, compact: bool = False, note: str | None = None):
    """Mirrors the printed challan layout: school header with a prominent
    logo on the right, student info block, a Month/Charge—Total—Paid—Pending
    grid (every pending month plus open extra charges, ending in a Grand
    Total row), bank details, an optional note, and a sign/stamp line — with
    a dashed-line tear-off stub at the very bottom (the school's copy: name,
    class, father's name, total pending, and a blank box to write the
    amount collected) that the school cuts off and keeps."""
    school = _get_school(db)
    pad = 4 * mm if compact else 5 * mm
    font_title = 15 if compact else 21
    font_body = 9 if compact else 12
    font_small = 8 if compact else 10

    slip_h = 20 * mm if compact else 26 * mm
    cut_y = y0 + slip_h
    main_floor = cut_y + 2 * mm

    c.setLineWidth(1.1)
    c.rect(x0, y0, w, h)
    c.setLineWidth(0.6)

    y = y0 + h - pad
    logo_size = 20 * mm if compact else 30 * mm
    logo = logo_content(school)
    if logo:
        try:
            c.drawImage(
                ImageReader(io.BytesIO(logo[0])), x0 + w - pad - logo_size, y - logo_size,
                width=logo_size, height=logo_size, preserveAspectRatio=True, mask="auto", anchor="n",
            )
        except Exception:
            pass

    header_top = y
    name_w = w - 2 * pad - (logo_size + 3 * mm if logo else 0)
    c.setFont("Helvetica-Bold", font_title)
    c.drawString(x0 + pad, header_top - font_title, (school.name or "School")[:int(name_w / (font_title * 0.45))])
    c.setFont("Helvetica", font_small)
    c.drawString(x0 + pad, header_top - font_title - (6 * mm if compact else 7.5 * mm), (school.address or "")[:55])
    c.drawString(x0 + pad, header_top - font_title - (10.5 * mm if compact else 13 * mm), f"Phone: {school.phone or '-'}")
    y = header_top - (21 * mm if compact else 27 * mm)
    c.line(x0 + pad, y, x0 + w - pad, y)
    y -= (5 * mm if compact else 6.5 * mm)

    info_rows = [
        ("Reg No:", student.registration_no),
        ("Name:", student.name),
        ("Class:", student.class_name),
        ("Father Name:", student.father_name),
        ("Monthly Fee:", f"Rs. {data['monthly_fee']:,.1f}"),
        ("Discount:", f"{data['discount_pct']:.1f}%" if data["discount_pct"] > 0 else "-"),
    ]
    label_x = x0 + pad
    value_x = x0 + pad + (32 * mm if compact else 44 * mm)
    row_h = 5 * mm if compact else 6.8 * mm
    for label, value in info_rows:
        c.setFont("Helvetica-Bold", font_body)
        c.drawString(label_x, y, label)
        c.setFont("Helvetica", font_body)
        c.drawString(value_x, y, str(value))
        y -= row_h
    # The loop's last decrement put y a full row_h below Discount's
    # baseline — claw most of that back so the line sits close beneath it.
    y += row_h - (2.5 * mm if compact else 3 * mm)
    c.line(x0 + pad, y, x0 + w - pad, y)
    y -= (1 * mm if compact else 1.3 * mm)

    rows = data["rows"]
    table_top = y
    col_x = [x0 + pad, x0 + pad + (w - 2 * pad) * 0.40, x0 + pad + (w - 2 * pad) * 0.62, x0 + pad + (w - 2 * pad) * 0.81, x0 + w - pad]
    default_row_h = 5.5 * mm if compact else 7.5 * mm
    min_row_h = 3.4 * mm if compact else 4 * mm

    # No QR on the main/student copy any more — it's printed only on the
    # school-copy stub below. The footer just needs the bank + note + sign lines.
    footer_reserve = pad + (9 * mm if compact else 13 * mm) + (5.5 * mm if compact else 6.5 * mm)
    table_rows_total = len(rows) + 2  # header + grand total
    available_for_table = table_top - (main_floor + footer_reserve)
    table_row_h = max(min_row_h, min(default_row_h, available_for_table / table_rows_total))
    shrink = table_row_h < 4.4 * mm
    row_font_small = font_small - 1.5 if shrink else font_small
    row_font_body = font_body - 1 if shrink else font_body
    table_bottom = table_top - table_rows_total * table_row_h

    c.rect(col_x[0], table_bottom, col_x[-1] - col_x[0], table_top - table_bottom)
    for x in col_x[1:-1]:
        c.line(x, table_bottom, x, table_top)

    def _table_row(top_y, label, total_s, paid_s, pending_s, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", row_font_body if bold else row_font_small)
        text_y = top_y - table_row_h + table_row_h * 0.32
        c.drawString(col_x[0] + 2 * mm, text_y, str(label)[:26])
        c.drawRightString(col_x[2] - 2 * mm, text_y, str(total_s))
        c.drawRightString(col_x[3] - 2 * mm, text_y, str(paid_s))
        c.drawRightString(col_x[4] - 2 * mm, text_y, str(pending_s))
        c.line(col_x[0], top_y - table_row_h, col_x[-1], top_y - table_row_h)

    row_y = table_top
    _table_row(row_y, "Month/Charge", "Total Fee", "Paid", "Pending", bold=True)
    row_y -= table_row_h
    c.setLineWidth(1.1)
    c.line(col_x[0], row_y, col_x[-1], row_y)
    c.setLineWidth(0.6)
    for label, total, paid, pending in rows:
        _table_row(row_y, label, f"{total:,.1f}", f"{paid:,.1f}", f"{pending:,.1f}")
        row_y -= table_row_h
    _table_row(row_y, "Grand Total", f"{data['grand_total']:,.1f}", f"{data['grand_paid']:,.1f}", f"{data['grand_pending']:,.1f}", bold=True)

    y = table_bottom - (4.5 * mm if compact else 6 * mm)
    c.setFont("Helvetica-Bold", font_small)
    c.drawString(x0 + pad, y, "Bank:")
    c.setFont("Helvetica", font_small)
    c.drawString(
        x0 + pad + 11 * mm, y,
        f"{school.bank_name or '-'}  |  {school.account_title or '-'}  |  {school.account_number or '-'}",
    )
    y -= (6 * mm if compact else 7.5 * mm)

    note_text = _clean_text(note or "Late fee may apply for overdue payments.")
    c.setFont("Helvetica-Bold", font_small)
    c.drawString(x0 + pad, y, "Note:")
    c.setFont("Helvetica", font_small)
    c.drawString(x0 + pad + 11 * mm, y, note_text[:55 if compact else 80])
    y -= (5.5 * mm if compact else 7 * mm)

    # Sign/stamp line sits just beneath the note. The QR is generated here only
    # so the school-copy stub below can reuse it — it is NOT drawn on this
    # student/parent portion of the slip.
    footer_y = max(y - (6 * mm if compact else 8 * mm), main_floor)

    qr_voucher = data["qr_voucher"]
    qr_path = None
    if qr_voucher is not None:
        try:
            qr_text = qr_service.get_or_create_qr_text(db, qr_voucher, student)
            qr_path = qr_service.generate_qr_image(qr_text)
        except Exception:
            qr_path = None

    c.setFont("Helvetica", font_small)
    c.drawRightString(x0 + w - pad, footer_y + 3 * mm, "Sign/Stamp: ____________________")

    # ---- Cut line ----
    c.saveState()
    c.setDash(3, 2)
    c.setLineWidth(0.8)
    c.line(x0 + 3 * mm, cut_y, x0 + w - 3 * mm, cut_y)
    c.restoreState()
    c.setFont("Helvetica", 7 if compact else 7.5)
    c.drawCentredString(x0 + w / 2, cut_y + 1 * mm, "✂  - - - - - - - - - -  Cut Here — School Copy Below  - - - - - - - - - -  ✂")

    # ---- Tear-off stub (school's copy) ----
    slip_pad = 3 * mm
    slip_font_label = 7.5 if compact else 8.5
    slip_font_body = 7.5 if compact else 9
    divider_x = x0 + w * 0.64

    sy = cut_y - (5 * mm if compact else 6 * mm)
    c.setFont("Helvetica-Bold", slip_font_label)
    c.drawString(x0 + slip_pad, sy, "Fee Receipt — School Copy")
    sy -= (4.5 * mm if compact else 5.5 * mm)

    c.setFont("Helvetica", slip_font_body)
    c.drawString(x0 + slip_pad, sy, f"Name: {student.name}")
    c.drawString(x0 + slip_pad + (30 * mm if compact else 38 * mm), sy, f"Class: {student.class_name}")
    sy -= (4 * mm if compact else 4.8 * mm)
    c.drawString(x0 + slip_pad, sy, f"Father: {student.father_name}")
    sy -= (4 * mm if compact else 4.8 * mm)
    c.setFont("Helvetica-Bold", slip_font_body)
    c.drawString(x0 + slip_pad, sy, f"Total Pending: Rs. {data['grand_pending']:,.1f}")

    c.line(divider_x, y0 + 2 * mm, divider_x, cut_y - 2 * mm)

    # Two small stacked boxes on the right: Remarks above, Amount Received below.
    box_x0 = divider_x + 3 * mm
    box_w = (x0 + w - slip_pad) - box_x0
    label_h = 3 * mm if compact else 3.5 * mm
    top_edge = cut_y - 2 * mm
    bottom_edge = y0 + 2 * mm
    half_h = (top_edge - bottom_edge) / 2

    remarks_label_y = top_edge - (2.3 * mm if compact else 2.8 * mm)
    remarks_box_top = top_edge - label_h
    remarks_box_bottom = top_edge - half_h + 0.8 * mm
    c.setFont("Helvetica-Bold", slip_font_label)
    c.drawString(box_x0, remarks_label_y, "Remarks:")
    c.rect(box_x0, remarks_box_bottom, box_w, remarks_box_top - remarks_box_bottom)

    amount_section_top = top_edge - half_h
    amount_label_y = amount_section_top - (2.3 * mm if compact else 2.8 * mm)
    amount_box_top = amount_section_top - label_h
    c.setFont("Helvetica-Bold", slip_font_label)
    c.drawString(box_x0, amount_label_y, "Amount Received (Rs.)")
    c.rect(box_x0, bottom_edge, box_w, amount_box_top - bottom_edge)

    # QR on the school copy too — placed in the free space between the info text
    # block and the remarks/amount divider, vertically centred in the stub.
    if qr_path is not None:
        try:
            copy_qr = 12 * mm if compact else 17 * mm
            copy_qr = min(copy_qr, slip_h - 2 * mm)
            copy_qr_x = divider_x - 3 * mm - copy_qr
            copy_qr_y = y0 + (slip_h - copy_qr) / 2
            c.drawImage(qr_path, copy_qr_x, copy_qr_y, width=copy_qr, height=copy_qr)
            c.setFont("Helvetica", slip_font_label - 1)
            c.drawCentredString(copy_qr_x + copy_qr / 2, copy_qr_y - 2.6 * mm, "Scan for fees")
        except Exception:
            pass

    # Temp QR image was reused for both the main receipt and the school copy —
    # remove it now that both have been drawn.
    if qr_path is not None:
        try:
            os.remove(qr_path)
        except OSError:
            pass


def generate_single_voucher_pdf(db: Session, student: Student, voucher: FeeVoucher, dest_path: str, note: str | None = None) -> str:
    data = gather_voucher_data(db, student, voucher)
    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    margin = 6 * mm
    _draw_receipt(c, db, margin, margin, width - 2 * margin, height - 2 * margin, student, data, note=note)
    c.showPage()
    c.save()
    return dest_path


def generate_individual_pages_pdf(db: Session, student_voucher_pairs: list[tuple[Student, FeeVoucher]], dest_path: str, note: str | None = None) -> str:
    """One full-size A4 receipt per page, for every voucher in the list."""
    if not student_voucher_pairs:
        raise ValueError("No vouchers to generate.")

    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    margin = 6 * mm
    for student, voucher in student_voucher_pairs:
        data = gather_voucher_data(db, student, voucher)
        _draw_receipt(c, db, margin, margin, width - 2 * margin, height - 2 * margin, student, data, note=note)
        c.showPage()
    c.save()
    return dest_path


def generate_4_per_sheet_pdf(db: Session, student_voucher_pairs: list[tuple[Student, FeeVoucher]], dest_path: str, note: str | None = None) -> str:
    """Lays out up to 4 vouchers per A4 page, continuing onto more pages as needed."""
    if not student_voucher_pairs:
        raise ValueError("No vouchers to generate.")

    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    margin = 4 * mm
    gap = 2 * mm
    cell_w = (width - 2 * margin - gap) / 2
    cell_h = (height - 2 * margin - gap) / 2
    positions = [
        (margin, margin + cell_h + gap),
        (margin + cell_w + gap, margin + cell_h + gap),
        (margin, margin),
        (margin + cell_w + gap, margin),
    ]

    for i, (student, voucher) in enumerate(student_voucher_pairs):
        pos_idx = i % 4
        if pos_idx == 0 and i > 0:
            c.showPage()
        x0, y0 = positions[pos_idx]
        data = gather_voucher_data(db, student, voucher)
        _draw_receipt(c, db, x0, y0, cell_w, cell_h, student, data, compact=True, note=note)

    c.showPage()
    c.save()
    return dest_path


def _students_with_dues(db: Session, students: list[Student]) -> list[tuple[Student, dict]]:
    pairs = []
    for student in students:
        data = gather_student_dues(db, student)
        if data["rows"]:
            pairs.append((student, data))
    return pairs


def generate_all_dues_individual_pdf(db: Session, students: list[Student], dest_path: str, note: str | None = None) -> str:
    """One full-size A4 challan per student, listing every pending month plus
    open extra charges — skips students with nothing outstanding."""
    pairs = _students_with_dues(db, students)
    if not pairs:
        raise ValueError("No students with pending dues found.")

    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    margin = 6 * mm
    for student, data in pairs:
        _draw_receipt(c, db, margin, margin, width - 2 * margin, height - 2 * margin, student, data, note=note)
        c.showPage()
    c.save()
    return dest_path


def generate_all_dues_4_per_sheet_pdf(db: Session, students: list[Student], dest_path: str, note: str | None = None) -> str:
    """4 students' complete pending-dues challans per A4 sheet — skips
    students with nothing outstanding."""
    pairs = _students_with_dues(db, students)
    if not pairs:
        raise ValueError("No students with pending dues found.")

    c = canvas.Canvas(dest_path, pagesize=A4)
    width, height = A4
    margin = 4 * mm
    gap = 2 * mm
    cell_w = (width - 2 * margin - gap) / 2
    cell_h = (height - 2 * margin - gap) / 2
    positions = [
        (margin, margin + cell_h + gap),
        (margin + cell_w + gap, margin + cell_h + gap),
        (margin, margin),
        (margin + cell_w + gap, margin),
    ]

    for i, (student, data) in enumerate(pairs):
        pos_idx = i % 4
        if pos_idx == 0 and i > 0:
            c.showPage()
        x0, y0 = positions[pos_idx]
        _draw_receipt(c, db, x0, y0, cell_w, cell_h, student, data, compact=True, note=note)

    c.showPage()
    c.save()
    return dest_path
