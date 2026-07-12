from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_role
from app.models.fee_audit import FeeAuditLog

router = APIRouter(
    prefix="/api/fee-audit",
    tags=["fee_audit"],
    # Audit trail is sensitive — Admin only.
    dependencies=[Depends(require_role("Admin"))],
)


class FeeAuditOut(BaseModel):
    id: int
    created_at: datetime
    actor_username: str
    actor_role: str
    action: str
    target_type: str
    student_id: int | None
    student_name: str
    label: str
    amount: float | None
    reason: str | None
    note: str | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[FeeAuditOut])
def list_fee_audit(limit: int = 200, action: str = "", db: Session = Depends(get_db)):
    """Recent fee payment/discount/edit/delete actions, newest first."""
    query = select(FeeAuditLog).order_by(FeeAuditLog.created_at.desc())
    if action:
        query = query.where(FeeAuditLog.action == action)
    return db.execute(query.limit(min(limit, 1000))).scalars().all()
