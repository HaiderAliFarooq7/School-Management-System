from datetime import date, datetime

from sqlalchemy import Date, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CashHandover(Base):
    """A record that an accountant handed physical cash over to the admin.

    Collections (how much each accountant *received* from parents) are derived
    from ``fee_audit_log`` payment rows; this table records how much cash they
    then *handed in*. The difference (collected − handed over) is the balance the
    accountant still holds, reconciled per school (tenant DB).
    """

    __tablename__ = "cash_handover"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    # The accountant who collected and handed over the cash.
    accountant_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    accountant_username: Mapped[str] = mapped_column(String(50), default="")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    # The day the handover covers/occurred (defaults to today when recorded).
    handover_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Which admin recorded this handover.
    recorded_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_by_username: Mapped[str] = mapped_column(String(50), default="")
