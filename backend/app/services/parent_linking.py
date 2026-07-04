"""Links a parent's mobile number to their children, within one school's
(tenant) database.

The parent module deliberately avoids a hard parent↔student foreign key: a
single mobile number can belong to several students, contacts are entered by
office staff in inconsistent formats, and a parent account may exist before any
contact row is recorded. So the link is resolved at query time by matching the
normalized mobile number against both ``student_contact`` (phone-type contacts)
and the legacy ``student.phone`` column. The Session passed in is already scoped
to the correct tenant by ``get_db``.
"""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.student_contact import StudentContact

# Contact types (student_contact.contact_type) that hold a phone/mobile number.
_PHONE_CONTACT_TYPES = ("phone", "mobile", "whatsapp", "cell")


def normalize_mobile(raw: str | None) -> str:
    """Reduce a phone number to a comparable core: digits only, with a leading
    country code (92) or trunk 0 stripped down to the 10-digit national part.
    e.g. '+92 300 1234567', '0300-1234567', '923001234567' → '3001234567'."""
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("92") and len(digits) > 10:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) > 10:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else digits


def find_students_for_mobile(db: Session, mobile_number: str) -> list[Student]:
    """Every student in this school whose recorded contact matches this mobile."""
    core = normalize_mobile(mobile_number)
    if not core:
        return []

    contact_rows = db.execute(
        select(StudentContact.student_id, StudentContact.contact_value).where(
            StudentContact.contact_type.in_(_PHONE_CONTACT_TYPES)
        )
    ).all()
    matched_ids = {sid for sid, value in contact_rows if normalize_mobile(value) == core}

    phone_rows = db.execute(select(Student.student_id, Student.phone)).all()
    matched_ids |= {sid for sid, phone in phone_rows if normalize_mobile(phone) == core}

    if not matched_ids:
        return []

    students = db.execute(
        select(Student).where(Student.student_id.in_(matched_ids)).order_by(Student.name)
    ).scalars().all()
    return list(students)


def find_parent_mobiles_for_student(db: Session, student: Student) -> set[str]:
    """All normalized mobile numbers on record for a student — used to fan a
    per-student notification out to the right parent accounts."""
    mobiles: set[str] = set()
    core = normalize_mobile(student.phone)
    if core:
        mobiles.add(core)
    contact_values = db.execute(
        select(StudentContact.contact_value).where(
            StudentContact.student_id == student.student_id,
            StudentContact.contact_type.in_(_PHONE_CONTACT_TYPES),
        )
    ).scalars().all()
    for value in contact_values:
        c = normalize_mobile(value)
        if c:
            mobiles.add(c)
    return mobiles
