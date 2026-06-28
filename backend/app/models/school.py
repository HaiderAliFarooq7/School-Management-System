from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class School(Base):
    __tablename__ = "school"

    school_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    logo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_name: Mapped[str] = mapped_column(String(255), default="")
    account_title: Mapped[str] = mapped_column(String(255), default="")
    account_number: Mapped[str] = mapped_column(String(100), default="")
    iban: Mapped[str] = mapped_column(String(100), default="")
    fee_due_day: Mapped[int] = mapped_column(Integer, default=10)
    challan_note: Mapped[str | None] = mapped_column(String, nullable=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_gateway: Mapped[str] = mapped_column(String(255), default="")
    sms_api_key: Mapped[str] = mapped_column(String(255), default="")
    sms_api_secret: Mapped[str] = mapped_column(String(255), default="")
    sms_sender_id: Mapped[str] = mapped_column(String(100), default="")
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    smtp_server: Mapped[str] = mapped_column(String(255), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_email: Mapped[str] = mapped_column(String(255), default="")
    smtp_password: Mapped[str] = mapped_column(String(255), default="")

    # Communication module: auto-queue an Absent notification when a
    # teacher finishes marking attendance.
    auto_notify_absent: Mapped[bool] = mapped_column(Boolean, default=False)
