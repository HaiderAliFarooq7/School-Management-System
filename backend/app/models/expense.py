from datetime import date, datetime

from sqlalchemy import Date, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Staff salaries are just an expense with category "Salary" — keeping them in
# one table (rather than a separate payroll table) means profit/loss is a
# single SUM with no joins, and a salary payment is filtered by category
# wherever it needs to be shown on its own.
EXPENSE_CATEGORIES = [
    "Salary",
    "Utilities",
    "Rent",
    "Supplies",
    "Maintenance",
    "Transport",
    "Other",
]


class Expense(Base):
    """Money going *out* of the school — salaries, utilities, rent, supplies.

    Income is derived from ``fee_audit_log`` payment rows (the same source the
    Collections page reconciles against), so profit/loss for a period is
    simply collected − expenses over the same dates. Kept per school (tenant
    DB) like every other financial table.
    """

    __tablename__ = "expense"

    expense_id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    # The day the money actually went out (not when it was typed in).
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    # Staff member for a salary, vendor/supplier for everything else.
    paid_to: Mapped[str] = mapped_column(String(120), default="")
    # "YYYY-MM" — which month a salary covers. Null for non-salary expenses.
    for_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), default="Cash")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_by_username: Mapped[str] = mapped_column(String(50), default="")
