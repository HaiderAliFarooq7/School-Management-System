from datetime import datetime

from sqlalchemy import Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeeAuditLog(Base):
    """A concise, per-user audit trail of money-changing fee actions — who
    recorded a payment, who gave a discount and why, who edited/deleted a
    voucher or charge. Kept per school (tenant DB). Read-only in the UI.

    ``action`` ∈ payment | discount | edit | delete | generate
    ``target_type`` ∈ fee_voucher | extra_charge
    """

    __tablename__ = "fee_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_username: Mapped[str] = mapped_column(String(50), default="")
    actor_role: Mapped[str] = mapped_column(String(30), default="")
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_name: Mapped[str] = mapped_column(String(150), default="")
    label: Mapped[str] = mapped_column(String(120), default="")          # month or charge description
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
