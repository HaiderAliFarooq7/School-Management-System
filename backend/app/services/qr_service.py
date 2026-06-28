import os
import tempfile

import qrcode
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fee_voucher import FeeVoucher
from app.models.qr_code import QRCode
from app.models.student import Student


def build_qr_text(student: Student, voucher: FeeVoucher) -> str:
    return f"{student.registration_no}|{voucher.fee_month}|{float(voucher.total_amount):.2f}|{voucher.status}|VC-{voucher.voucher_id}"


def get_or_create_qr_text(db: Session, voucher: FeeVoucher, student: Student) -> str:
    existing = db.execute(
        select(QRCode.qr_code_text).where(QRCode.voucher_id == voucher.voucher_id)
    ).scalar_one_or_none()
    if existing:
        return existing
    text = build_qr_text(student, voucher)
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
