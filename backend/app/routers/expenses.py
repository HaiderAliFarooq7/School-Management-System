"""Admin-only school expenses & staff salaries.

Records money going *out* (salaries, utilities, rent, supplies) so the school's
real profit/loss is visible, not just fee income. Income in the summary comes
from ``fee_audit_log`` payment rows — the same source the Collections page
reconciles against — so the two pages always agree on what was collected.
"""
import re
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.expense import EXPENSE_CATEGORIES, Expense
from app.models.fee_audit import FeeAuditLog
from app.models.user import User

router = APIRouter(
    prefix="/api/expenses",
    tags=["expenses"],
    # School profit/loss and staff pay — Admin only, same as Collections.
    dependencies=[Depends(require_role("Admin"))],
)

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid {field} — use YYYY-MM-DD.")


def _date_bounds(date_from: str, date_to: str) -> tuple[date | None, date | None]:
    start = _parse_date(date_from, "date_from") if date_from else None
    end = _parse_date(date_to, "date_to") if date_to else None
    if start and end and start > end:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "date_from must not be after date_to.")
    return start, end


def _actor_display_name(db: Session, current_user: CurrentUser) -> str:
    if getattr(current_user, "is_super", False):
        return "superadmin"
    u = db.get(User, current_user.user_id)
    return u.username if u else ""


class ExpenseIn(BaseModel):
    expense_date: date
    category: str
    description: str = ""
    paid_to: str = ""
    for_month: str | None = None
    amount: float = Field(gt=0, description="Must be greater than zero.")
    payment_method: str = "Cash"
    note: str | None = None


class ExpenseOut(BaseModel):
    expense_id: int
    expense_date: date
    category: str
    description: str
    paid_to: str
    for_month: str | None
    amount: float
    payment_method: str
    note: str | None
    recorded_by_username: str


def _validate(payload: ExpenseIn) -> None:
    if payload.category not in EXPENSE_CATEGORIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown category {payload.category!r}. Expected one of: {', '.join(EXPENSE_CATEGORIES)}.",
        )
    if payload.for_month and not _MONTH_RE.match(payload.for_month):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "for_month must look like YYYY-MM (e.g. 2026-09).")


def _to_out(e: Expense) -> ExpenseOut:
    return ExpenseOut(
        expense_id=e.expense_id,
        expense_date=e.expense_date,
        category=e.category,
        description=e.description or "",
        paid_to=e.paid_to or "",
        for_month=e.for_month,
        amount=float(e.amount),
        payment_method=e.payment_method or "",
        note=e.note,
        recorded_by_username=e.recorded_by_username or "",
    )


@router.get("/categories", response_model=list[str])
def list_categories():
    """The allowed category values, so the UI dropdown and the server can
    never drift apart."""
    return EXPENSE_CATEGORIES


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    date_from: str = "",
    date_to: str = "",
    category: str = "",
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """Expenses in a date range, newest first."""
    start, end = _date_bounds(date_from, date_to)
    query = select(Expense).order_by(Expense.expense_date.desc(), Expense.expense_id.desc())
    if start is not None:
        query = query.where(Expense.expense_date >= start)
    if end is not None:
        query = query.where(Expense.expense_date <= end)
    if category:
        query = query.where(Expense.category == category)
    return [_to_out(e) for e in db.execute(query.limit(limit)).scalars()]


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseIn,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _validate(payload)
    expense = Expense(
        expense_date=payload.expense_date,
        category=payload.category,
        description=payload.description.strip(),
        paid_to=payload.paid_to.strip(),
        for_month=payload.for_month or None,
        amount=payload.amount,
        payment_method=payload.payment_method.strip() or "Cash",
        note=payload.note,
        recorded_by_user_id=getattr(current_user, "user_id", None),
        recorded_by_username=_actor_display_name(db, current_user),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _to_out(expense)


# Declared before the /{expense_id} routes so a future GET-by-id can never
# shadow /summary and /categories.
class CategoryTotal(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummary(BaseModel):
    income: float
    expenses: float
    net: float
    salary_total: float
    by_category: list[CategoryTotal]
    monthly: list[dict]


@router.get("/summary", response_model=ExpenseSummary)
def expense_summary(date_from: str = "", date_to: str = "", db: Session = Depends(get_db)):
    """Profit/loss for the range: fees actually collected minus expenses paid,
    with a per-category breakdown and a month-by-month income/expense series."""
    start, end = _date_bounds(date_from, date_to)

    cat_query = select(
        Expense.category, func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.expense_id)
    ).group_by(Expense.category)
    if start is not None:
        cat_query = cat_query.where(Expense.expense_date >= start)
    if end is not None:
        cat_query = cat_query.where(Expense.expense_date <= end)

    by_category = [
        CategoryTotal(category=cat, total=float(total or 0), count=count)
        for cat, total, count in db.execute(cat_query).all()
    ]
    by_category.sort(key=lambda r: r.total, reverse=True)
    expenses_total = sum(r.total for r in by_category)
    salary_total = sum(r.total for r in by_category if r.category == "Salary")

    # Income = non-voided payment rows in the audit log, matching Collections.
    income_query = select(func.coalesce(func.sum(FeeAuditLog.amount), 0)).where(
        FeeAuditLog.action == "payment", FeeAuditLog.voided.is_(False)
    )
    if start is not None:
        income_query = income_query.where(FeeAuditLog.created_at >= datetime.combine(start, time.min))
    if end is not None:
        income_query = income_query.where(FeeAuditLog.created_at <= datetime.combine(end, time.max))
    income = float(db.execute(income_query).scalar_one() or 0)

    # Month-by-month, so the UI can chart income vs expenses over the range.
    exp_by_month: dict[str, float] = {}
    month_query = select(
        func.to_char(Expense.expense_date, "YYYY-MM"), func.coalesce(func.sum(Expense.amount), 0)
    ).group_by(func.to_char(Expense.expense_date, "YYYY-MM"))
    if start is not None:
        month_query = month_query.where(Expense.expense_date >= start)
    if end is not None:
        month_query = month_query.where(Expense.expense_date <= end)
    for m, total in db.execute(month_query).all():
        exp_by_month[m] = float(total or 0)

    inc_by_month: dict[str, float] = {}
    inc_month_query = select(
        func.to_char(FeeAuditLog.created_at, "YYYY-MM"), func.coalesce(func.sum(FeeAuditLog.amount), 0)
    ).where(FeeAuditLog.action == "payment", FeeAuditLog.voided.is_(False)).group_by(
        func.to_char(FeeAuditLog.created_at, "YYYY-MM")
    )
    if start is not None:
        inc_month_query = inc_month_query.where(FeeAuditLog.created_at >= datetime.combine(start, time.min))
    if end is not None:
        inc_month_query = inc_month_query.where(FeeAuditLog.created_at <= datetime.combine(end, time.max))
    for m, total in db.execute(inc_month_query).all():
        inc_by_month[m] = float(total or 0)

    monthly = [
        {"month": m, "income": inc_by_month.get(m, 0.0), "expenses": exp_by_month.get(m, 0.0),
         "net": inc_by_month.get(m, 0.0) - exp_by_month.get(m, 0.0)}
        for m in sorted(set(exp_by_month) | set(inc_by_month))
    ]

    return ExpenseSummary(
        income=income,
        expenses=expenses_total,
        net=income - expenses_total,
        salary_total=salary_total,
        by_category=by_category,
        monthly=monthly,
    )


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseIn, db: Session = Depends(get_db)):
    _validate(payload)
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    expense.expense_date = payload.expense_date
    expense.category = payload.category
    expense.description = payload.description.strip()
    expense.paid_to = payload.paid_to.strip()
    expense.for_month = payload.for_month or None
    expense.amount = payload.amount
    expense.payment_method = payload.payment_method.strip() or "Cash"
    expense.note = payload.note
    db.commit()
    db.refresh(expense)
    return _to_out(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    db.delete(expense)
    db.commit()
