"""Records money-changing fee actions to the per-school fee_audit_log.

Best-effort: a logging failure must never break the actual payment/discount, so
callers stage the record in the same transaction they commit — and if resolving
the username hiccups, we still record the action with what we know.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.deps import CurrentUser
from app.models.fee_audit import FeeAuditLog
from app.models.student import Student
from app.models.user import User


def record(
    db: Session,
    current_user: CurrentUser | None,
    *,
    action: str,
    target_type: str,
    student: Student | None = None,
    label: str = "",
    amount: float | None = None,
    reason: str | None = None,
    note: str | None = None,
) -> None:
    """Stage an audit entry (the caller commits). Never raises."""
    try:
        username = ""
        role = ""
        user_id = None
        if current_user is not None:
            user_id = current_user.user_id
            role = current_user.role_name
            if getattr(current_user, "is_super", False):
                username = "superadmin"
            else:
                u = db.get(User, current_user.user_id)
                username = u.username if u else ""
        db.add(
            FeeAuditLog(
                actor_user_id=user_id,
                actor_username=username,
                actor_role=role,
                action=action,
                target_type=target_type,
                student_id=student.student_id if student is not None else None,
                student_name=student.name if student is not None else "",
                label=(label or "")[:120],
                amount=amount,
                reason=(reason or None),
                note=note,
            )
        )
    except Exception:  # noqa: BLE001 — auditing must never break the money action
        pass
