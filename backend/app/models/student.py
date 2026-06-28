from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Student(Base):
    __tablename__ = "student"

    student_id: Mapped[int] = mapped_column(primary_key=True)
    registration_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    father_name: Mapped[str] = mapped_column(String(150), nullable=False)
    class_name: Mapped[str] = mapped_column(
        String(50), ForeignKey("grade.class_name", onupdate="CASCADE"), nullable=False
    )
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    b_form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cnic: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    default_fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
