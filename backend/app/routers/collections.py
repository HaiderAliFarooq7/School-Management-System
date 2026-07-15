"""Admin-only collections & cash reconciliation.

Everything here is derived from the per-school ``fee_audit_log`` (who recorded
each payment, for which student, how much, when) plus the ``cash_handover``
table (how much cash each accountant physically handed back to the admin). Lets
the admin see, for any date range, which accountant collected what — and
reconcile it against the cash actually handed in.
"""
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.cash_handover import CashHandover
from app.models.fee_audit import FeeAuditLog
from app.models.role import Role
from app.models.user import User

router = APIRouter(
    prefix="/api/collections",
    tags=["collections"],
    # Money reconciliation across accountants — Admin only.
    dependencies=[Depends(require_role("Admin"))],
)


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid {field} — use YYYY-MM-DD.")


def _datetime_bounds(date_from: str, date_to: str) -> tuple[datetime | None, datetime | None]:
    """Turn optional YYYY-MM-DD strings into inclusive [start-of-day, end-of-day]."""
    start = datetime.combine(_parse_date(date_from, "date_from"), time.min) if date_from else None
    end = datetime.combine(_parse_date(date_to, "date_to"), time.max) if date_to else None
    return start, end


def _actor_display_name(db: Session, current_user: CurrentUser) -> str:
    if getattr(current_user, "is_super", False):
        return "superadmin"
    u = db.get(User, current_user.user_id)
    return u.username if u else ""


# ── Collections summary (per accountant, for a date range) ────────────────────

class CollectorRow(BaseModel):
    actor_user_id: int | None
    actor_username: str
    actor_role: str
    fee_collected: float
    charge_collected: float
    total_collected: float
    payment_count: int


class CollectionsSummary(BaseModel):
    rows: list[CollectorRow]
    fee_collected: float
    charge_collected: float
    total_collected: float
    payment_count: int


@router.get("/summary", response_model=CollectionsSummary)
def collections_summary(date_from: str = "", date_to: str = "", db: Session = Depends(get_db)):
    """How much each accountant collected (fees vs extra charges) in the range."""
    start, end = _datetime_bounds(date_from, date_to)
    query = (
        select(
            FeeAuditLog.actor_user_id,
            FeeAuditLog.actor_username,
            FeeAuditLog.actor_role,
            FeeAuditLog.target_type,
            func.coalesce(func.sum(FeeAuditLog.amount), 0),
            func.count(FeeAuditLog.id),
        )
        .where(FeeAuditLog.action == "payment")
        .group_by(
            FeeAuditLog.actor_user_id,
            FeeAuditLog.actor_username,
            FeeAuditLog.actor_role,
            FeeAuditLog.target_type,
        )
    )
    if start is not None:
        query = query.where(FeeAuditLog.created_at >= start)
    if end is not None:
        query = query.where(FeeAuditLog.created_at <= end)

    agg: dict[int | None, dict] = {}
    for user_id, username, role, target_type, amount, count in db.execute(query).all():
        rec = agg.setdefault(
            user_id,
            {"username": username or "", "role": role or "", "fee": 0.0, "charge": 0.0, "count": 0},
        )
        amt = float(amount or 0)
        if target_type == "extra_charge":
            rec["charge"] += amt
        else:
            rec["fee"] += amt
        rec["count"] += count

    rows = [
        CollectorRow(
            actor_user_id=user_id,
            actor_username=rec["username"],
            actor_role=rec["role"],
            fee_collected=rec["fee"],
            charge_collected=rec["charge"],
            total_collected=rec["fee"] + rec["charge"],
            payment_count=rec["count"],
        )
        for user_id, rec in agg.items()
    ]
    rows.sort(key=lambda r: r.total_collected, reverse=True)

    return CollectionsSummary(
        rows=rows,
        fee_collected=sum(r.fee_collected for r in rows),
        charge_collected=sum(r.charge_collected for r in rows),
        total_collected=sum(r.total_collected for r in rows),
        payment_count=sum(r.payment_count for r in rows),
    )


# ── Payment detail (student-by-student, for drill-down) ───────────────────────

class PaymentDetailRow(BaseModel):
    id: int
    created_at: datetime
    actor_user_id: int | None
    actor_username: str
    student_id: int | None
    student_name: str
    target_type: str
    label: str
    amount: float | None

    model_config = {"from_attributes": True}


@router.get("/detail", response_model=list[PaymentDetailRow])
def collections_detail(
    actor_user_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    limit: int = 500,
    db: Session = Depends(get_db),
):
    """Individual payments (which student, how much, when) — newest first.
    Optionally scoped to one accountant for the drill-down view."""
    start, end = _datetime_bounds(date_from, date_to)
    query = select(FeeAuditLog).where(FeeAuditLog.action == "payment")
    if actor_user_id is not None:
        query = query.where(FeeAuditLog.actor_user_id == actor_user_id)
    if start is not None:
        query = query.where(FeeAuditLog.created_at >= start)
    if end is not None:
        query = query.where(FeeAuditLog.created_at <= end)
    query = query.order_by(FeeAuditLog.created_at.desc()).limit(min(limit, 2000))
    return db.execute(query).scalars().all()


# ── Reconciliation (all-time collected vs handed over) ────────────────────────

class ReconciliationRow(BaseModel):
    actor_user_id: int | None
    actor_username: str
    actor_role: str
    total_collected: float
    total_handed_over: float
    balance: float


@router.get("/reconciliation", response_model=list[ReconciliationRow])
def reconciliation(db: Session = Depends(get_db)):
    """Per accountant, all-time: total collected minus total cash handed in.
    ``balance`` is the cash the accountant is still holding (owes the office)."""
    data: dict[int | None, dict] = {}

    # Seed with every active accountant so someone who hasn't collected yet
    # still shows up with a zero balance.
    accountants = db.execute(
        select(User, Role).join(Role, Role.role_id == User.role_id).where(Role.role_name == "Accountant")
    ).all()
    for user, role in accountants:
        data[user.user_id] = {
            "username": user.username, "role": role.role_name, "collected": 0.0, "handed": 0.0,
        }

    collected = db.execute(
        select(
            FeeAuditLog.actor_user_id,
            func.max(FeeAuditLog.actor_username),
            func.max(FeeAuditLog.actor_role),
            func.coalesce(func.sum(FeeAuditLog.amount), 0),
        )
        .where(FeeAuditLog.action == "payment")
        .group_by(FeeAuditLog.actor_user_id)
    ).all()
    for user_id, username, role, total in collected:
        rec = data.setdefault(user_id, {"username": username or "", "role": role or "", "collected": 0.0, "handed": 0.0})
        rec["collected"] += float(total or 0)

    handed = db.execute(
        select(
            CashHandover.accountant_user_id,
            func.max(CashHandover.accountant_username),
            func.coalesce(func.sum(CashHandover.amount), 0),
        ).group_by(CashHandover.accountant_user_id)
    ).all()
    for user_id, username, total in handed:
        rec = data.setdefault(user_id, {"username": username or "", "role": "", "collected": 0.0, "handed": 0.0})
        rec["handed"] += float(total or 0)
        if not rec["username"]:
            rec["username"] = username or ""

    rows = [
        ReconciliationRow(
            actor_user_id=user_id,
            actor_username=rec["username"],
            actor_role=rec["role"],
            total_collected=rec["collected"],
            total_handed_over=rec["handed"],
            balance=rec["collected"] - rec["handed"],
        )
        for user_id, rec in data.items()
    ]
    rows.sort(key=lambda r: r.balance, reverse=True)
    return rows


# ── Cash handover records ─────────────────────────────────────────────────────

class HandoverCreate(BaseModel):
    accountant_user_id: int
    amount: float
    handover_date: str | None = None  # YYYY-MM-DD; defaults to today
    note: str | None = None


class HandoverOut(BaseModel):
    id: int
    created_at: datetime
    accountant_user_id: int | None
    accountant_username: str
    amount: float
    handover_date: date
    note: str | None
    recorded_by_username: str

    model_config = {"from_attributes": True}


@router.get("/handovers", response_model=list[HandoverOut])
def list_handovers(
    actor_user_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    limit: int = 300,
    db: Session = Depends(get_db),
):
    """Recorded cash handovers, newest first — optionally filtered."""
    query = select(CashHandover).order_by(CashHandover.handover_date.desc(), CashHandover.id.desc())
    if actor_user_id is not None:
        query = query.where(CashHandover.accountant_user_id == actor_user_id)
    if date_from:
        query = query.where(CashHandover.handover_date >= _parse_date(date_from, "date_from"))
    if date_to:
        query = query.where(CashHandover.handover_date <= _parse_date(date_to, "date_to"))
    return db.execute(query.limit(min(limit, 1000))).scalars().all()


@router.post("/handovers", response_model=HandoverOut)
def create_handover(
    payload: HandoverCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin records that an accountant handed over a sum of cash."""
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Amount must be greater than zero.")
    accountant = db.get(User, payload.accountant_user_id)
    if accountant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Accountant not found.")
    when = _parse_date(payload.handover_date, "handover_date") if payload.handover_date else date.today()

    record = CashHandover(
        accountant_user_id=accountant.user_id,
        accountant_username=accountant.username,
        amount=payload.amount,
        handover_date=when,
        note=(payload.note or None),
        recorded_by_user_id=current_user.user_id,
        recorded_by_username=_actor_display_name(db, current_user),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/handovers/{handover_id}")
def delete_handover(handover_id: int, db: Session = Depends(get_db)):
    """Remove a mistakenly-entered handover."""
    record = db.get(CashHandover, handover_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Handover record not found.")
    db.delete(record)
    db.commit()
    return {"detail": "Deleted"}
