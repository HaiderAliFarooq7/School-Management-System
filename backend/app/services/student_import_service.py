"""Commercial-grade student bulk import: column auto-mapping, class-name
normalization, phone normalization, row validation, and the actual import
transaction. Built to handle arbitrary spreadsheet formats — not just one
school's export — via synonym-based auto-mapping with a manual fallback."""
import re
from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.payment_history import PaymentHistory
from app.models.qr_code import QRCode
from app.models.student import Student
from app.models.student_contact import StudentContact
from app.schemas.student_import import IMPORT_FIELDS, ExecuteError, ExecuteResult, PreviewRow

# --------------------------------------------------------------- column mapping
_FIELD_SYNONYMS: dict[str, str] = {
    "name": "name", "studentname": "name", "students_name": "name", "fullname": "name",
    "fathername": "father_name", "guardianname": "father_name", "fathersname": "father_name",
    "guardian": "father_name", "parentname": "father_name",
    "class": "class_name", "studentclass": "class_name", "grade": "class_name", "classname": "class_name", "section": "class_name",
    "phone": "phone", "mobileno": "phone", "mobile": "phone", "contact": "phone", "contactno": "phone",
    "guardianphone": "phone", "parentphone": "phone", "phoneno": "phone", "cellno": "phone", "cellphone": "phone",
    "cnic": "cnic", "fathercnic": "cnic", "guardiancnic": "cnic", "nic": "cnic", "cnicno": "cnic",
    "monthlyfee": "default_fee", "fee": "default_fee", "defaultfee": "default_fee", "tuitionfee": "default_fee", "feeamount": "default_fee",
    "dob": "dob", "dateofbirth": "dob", "birthdate": "dob", "birthday": "dob",
    "admissiondate": "admission_date", "dateofadmission": "admission_date", "admdate": "admission_date",
    "bformno": "b_form", "bform": "b_form", "bformnumber": "b_form", "bformno.": "b_form",
    "address": "address", "homeaddress": "address",
    "status": "status",
    "registrationno": "registration_no", "regno": "registration_no", "registrationnumber": "registration_no",
    "regnumber": "registration_no", "registration": "registration_no", "studentid": "registration_no", "rollno": "registration_no",
}


def _normalize_key(s: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", s.lower())


def suggest_column_mapping(columns: list[str]) -> dict[str, str | None]:
    return {col: _FIELD_SYNONYMS.get(_normalize_key(col)) for col in columns}


# ---------------------------------------------------------------- class names
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def _canonical_class_guess(raw: str, known_classes: list[str]) -> str | None:
    if not raw:
        return None
    norm = re.sub(r"[^a-z0-9]", "", raw.strip().lower())
    for kc in known_classes:
        if re.sub(r"[^a-z0-9]", "", kc.lower()) == norm:
            return kc
    if norm in ("playgroup", "pg"):
        return "Playgroup" if "Playgroup" in known_classes else None
    if norm == "nursery":
        return "Nursery" if "Nursery" in known_classes else None
    if norm in ("prep", "kg", "kindergarten"):
        return "Prep" if "Prep" in known_classes else None
    if norm in _NUMBER_WORDS:
        candidate = f"Grade {_NUMBER_WORDS[norm]}"
        return candidate if candidate in known_classes else None
    digits = re.sub(r"\D", "", norm)
    if digits and digits.isdigit():
        candidate = f"Grade {int(digits)}"
        if candidate in known_classes:
            return candidate
    return None


def suggest_class_mapping(distinct_values: list[str], known_classes: list[str]) -> dict[str, str | None]:
    return {v: _canonical_class_guess(v, known_classes) for v in distinct_values}


# -------------------------------------------------------------------- phones
def normalize_phone(raw: object) -> str | None:
    """Normalizes any recognizable Pakistani mobile number to 92XXXXXXXXXX.
    Returns None if the value is empty or not a recognizable phone number."""
    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    if digits.startswith("92") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 11:
        return "92" + digits[1:]
    if len(digits) == 10 and digits.startswith("3"):
        return "92" + digits
    return None


# ----------------------------------------------------------------------- misc
def _parse_date(raw: object) -> date | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _clean_str(raw: object) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _parse_fee(raw: object) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return max(float(raw), 0)
    except (TypeError, ValueError):
        return None


def _map_row(
    row: dict, mapping: dict[str, str], class_value_mapping: dict[str, str],
) -> tuple[dict, list[str], list[str]]:
    """Applies the column mapping + normalization to one raw Excel row.
    Returns (mapped_fields, errors, missing_fields)."""
    fields: dict = {}
    for excel_col, our_field in mapping.items():
        if our_field and our_field in IMPORT_FIELDS:
            fields[our_field] = row.get(excel_col)

    errors: list[str] = []
    missing: list[str] = []

    name = _clean_str(fields.get("name"))
    if not name:
        errors.append("Missing student name")
    fields["name"] = name

    father_name = _clean_str(fields.get("father_name")) or ""
    if not father_name:
        missing.append("father_name")
    fields["father_name"] = father_name

    raw_class = _clean_str(fields.get("class_name"))
    canonical_class = class_value_mapping.get(raw_class or "") if raw_class else None
    if not canonical_class:
        errors.append(f"Unrecognized class '{raw_class}'" if raw_class else "Missing class")
    fields["class_name"] = canonical_class

    phone_raw = fields.get("phone")
    phone = normalize_phone(phone_raw)
    if phone_raw and not phone:
        missing.append("phone")  # present but unrecognizable — dropped, not a hard failure
    elif not phone_raw:
        missing.append("phone")
    fields["phone"] = phone

    cnic = _clean_str(fields.get("cnic"))
    if not cnic:
        missing.append("cnic")
    fields["cnic"] = cnic

    fee = _parse_fee(fields.get("default_fee"))
    if fee is None:
        missing.append("default_fee")
    fields["default_fee"] = fee

    fields["dob"] = _parse_date(fields.get("dob"))
    fields["admission_date"] = _parse_date(fields.get("admission_date"))
    fields["b_form"] = _clean_str(fields.get("b_form"))
    fields["address"] = _clean_str(fields.get("address"))

    status = _clean_str(fields.get("status")) or "Active"
    fields["status"] = "Inactive" if status.lower().startswith("in") else "Active"

    fields["registration_no"] = _clean_str(fields.get("registration_no"))

    return fields, errors, missing


def build_preview_rows(
    raw_rows: list[dict], mapping: dict[str, str], class_value_mapping: dict[str, str],
) -> list[PreviewRow]:
    seen_regs: dict[str, int] = {}
    rows: list[PreviewRow] = []
    for i, raw in enumerate(raw_rows, start=1):
        fields, errors, missing = _map_row(raw, mapping, class_value_mapping)
        reg_no = fields.get("registration_no")

        status: str = "valid"
        if reg_no:
            if reg_no in seen_regs:
                status = "duplicate"
                errors.append(f"Duplicate registration number '{reg_no}' (first seen at row {seen_regs[reg_no]})")
            else:
                seen_regs[reg_no] = i
        if errors and status != "duplicate":
            status = "invalid"
        elif errors and status == "duplicate":
            pass  # duplicate already takes priority for display

        rows.append(PreviewRow(row_number=i, data=fields, status=status, errors=errors, missing_fields=missing))
    return rows


def _generate_registration_no(db: Session) -> str:
    last = db.execute(
        select(Student.registration_no).order_by(Student.student_id.desc()).limit(1)
    ).scalar_one_or_none()
    if last is None:
        return "REG-0001"
    digits = "".join(ch for ch in last if ch.isdigit())
    next_num = (int(digits) + 1) if digits else 1
    return f"REG-{next_num:04d}"


def wipe_all_student_data(db: Session) -> None:
    """Deletes every student and all dependent records, in the correct order,
    inside the caller's transaction (no commit here). Mirrors the existing
    /api/backup/reset endpoint's cleanup, plus attendance explicitly."""
    for model in (QRCode, StudentContact, PaymentHistory, ExtraCharge, FeeVoucher, AttendanceRecord, Student):
        db.execute(delete(model))


def execute_import(
    db: Session,
    raw_rows: list[dict],
    mapping: dict[str, str],
    class_value_mapping: dict[str, str],
    import_mode: str,
    only_valid_rows: bool,
) -> ExecuteResult:
    preview = build_preview_rows(raw_rows, mapping, class_value_mapping)

    if import_mode == "delete_all":
        wipe_all_student_data(db)

    existing_by_reg: dict[str, Student] = {}
    if import_mode != "delete_all":
        existing = db.execute(select(Student)).scalars().all()
        existing_by_reg = {s.registration_no: s for s in existing}

    imported = updated = skipped = failed = 0
    errors: list[ExecuteError] = []

    for row in preview:
        if row.status == "invalid":
            failed += 1
            errors.append(ExecuteError(row_number=row.row_number, reason="; ".join(row.errors) or "Invalid row"))
            continue
        if row.status == "duplicate":
            skipped += 1
            continue
        if only_valid_rows and row.errors:
            failed += 1
            errors.append(ExecuteError(row_number=row.row_number, reason="; ".join(row.errors)))
            continue

        data = row.data
        reg_no = data.get("registration_no")
        existing_student = existing_by_reg.get(reg_no) if reg_no else None

        try:
            with db.begin_nested():  # SAVEPOINT — a bad row only rolls back itself, not the whole import
                if existing_student is not None:
                    if import_mode == "new_only":
                        skipped += 1
                        continue
                    # update_or_add (or delete_all, where existing_student is always None anyway)
                    existing_student.name = data["name"]
                    existing_student.father_name = data["father_name"]
                    existing_student.class_name = data["class_name"]
                    existing_student.dob = data["dob"]
                    existing_student.admission_date = data["admission_date"]
                    existing_student.b_form = data["b_form"]
                    existing_student.cnic = data["cnic"]
                    existing_student.phone = data["phone"]
                    existing_student.address = data["address"]
                    existing_student.default_fee = data["default_fee"]
                    existing_student.status = data["status"]
                    db.flush()
                    updated += 1
                    continue

                final_reg_no = reg_no or _generate_registration_no(db)
                student = Student(
                    registration_no=final_reg_no,
                    name=data["name"],
                    father_name=data["father_name"],
                    class_name=data["class_name"],
                    dob=data["dob"],
                    admission_date=data["admission_date"],
                    b_form=data["b_form"],
                    cnic=data["cnic"],
                    phone=data["phone"],
                    address=data["address"],
                    default_fee=data["default_fee"],
                    status=data["status"],
                )
                db.add(student)
                db.flush()
                if reg_no:
                    existing_by_reg[reg_no] = student
                imported += 1
        except Exception as exc:
            failed += 1
            errors.append(ExecuteError(row_number=row.row_number, reason=str(exc)))

    db.commit()
    return ExecuteResult(imported=imported, updated=updated, skipped=skipped, failed=failed, errors=errors)
