from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeeVoucher(Base):
    __tablename__ = "fee_voucher"
    __table_args__ = (UniqueConstraint("student_id", "fee_month"),)

    voucher_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False
    )
    fee_month: Mapped[str] = mapped_column(String(20), nullable=False)
    fee_month_sort: Mapped[str] = mapped_column(String(7), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Unpaid")

    @property
    def remaining(self) -> float:
        return max(float(self.total_amount) - float(self.paid_amount) - float(self.discount_amount), 0)
