from sqlalchemy import Integer, String
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
