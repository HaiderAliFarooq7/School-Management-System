from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    __table_args__ = (
        UniqueConstraint("student_id", "attendance_date", "period_name"),
        CheckConstraint("status IN ('Present','Absent','Late','Leave')"),
    )

    attendance_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False
    )
    class_name: Mapped[str] = mapped_column(
        String(50), ForeignKey("grade.class_name", onupdate="CASCADE"), nullable=False
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_name: Mapped[str] = mapped_column(String(50), default="Full Day")
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    remarks: Mapped[str | None] = mapped_column(String, nullable=True)
    marked_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.user_id"), nullable=True
    )
    marked_at: Mapped[datetime] = mapped_column(server_default=func.now())
