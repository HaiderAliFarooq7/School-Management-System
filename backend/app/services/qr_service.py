import os
import tempfile

import qrcode
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.fee_voucher import FeeVoucher
from app.models.qr_code import QRCode
from app.models.student import Student


def build_qr_text(student: Student, voucher: FeeVoucher) -> str:
    """The challan QR encodes a direct link to the student's fee page, so
    scanning it with ANY camera (phone camera app, laptop webcam, the in-app
    scanner) opens that student's complete fee ledger. The voucher id rides
    along as a query param for context. Older printed challans used a plain
    'REG-xxxx|month|amount|status|VC-id' data payload — the in-app scanner
    still understands those."""
    return f"{settings.app_base_url}/fees/student/{student.student_id}?v={voucher.voucher_id}"


def get_or_create_qr_text(db: Session, voucher: FeeVoucher, student: Student) -> str:
    row = db.execute(
        select(QRCode).where(QRCode.voucher_id == voucher.voucher_id)
    ).scalar_one_or_none()
    text = build_qr_text(student, voucher)
    if row is not None:
        # Upgrade legacy data-payload QRs to the URL format the next time the
        # challan is printed, so reprints become phone-camera scannable.
        if row.qr_code_text != text:
            row.qr_code_text = text
            db.commit()
        return text
    db.add(QRCode(voucher_id=voucher.voucher_id, qr_code_text=text))
    db.commit()
    return text


def generate_qr_image(text: str) -> str:
    img = qrcode.make(text)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


def lookup_voucher_by_qr_text(db: Session, qr_text: str) -> int | None:
    return db.execute(
        select(QRCode.voucher_id).where(QRCode.qr_code_text == qr_text)
    ).scalar_one_or_none()
