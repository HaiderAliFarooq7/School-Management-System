"""Notification orchestration for the parent module.

One entry point — :func:`dispatch_notification` — used by both automatic sends
(a student marked absent) and manual admin/accountant sends (fee reminder,
announcement). It operates entirely within a single school's (tenant) Session,
so parents, devices and students are all in the same tenant database. It:

  1. resolves the recipient parent accounts for the requested audience
     (a single student, a class, or the whole school),
  2. writes one ``parent_notification`` inbox row per recipient (the history the
     app shows, and the offline source of truth),
  3. pushes to every active device via FCM (best-effort; skipped cleanly when
     Firebase isn't configured), deactivating tokens FCM reports as invalid,
  4. records a single ``notification_log`` audit row with delivery counts.

Everything except the FCM push is staged in the caller's session; the caller
commits.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_log import NotificationLog
from app.models.parent_account import ParentAccount
from app.models.parent_device import ParentDevice
from app.models.parent_notification import ParentNotification
from app.models.student import Student
from app.services import firebase_service
from app.services.parent_linking import find_parent_mobiles_for_student, normalize_mobile

# Notification type constants (kept in sync with the Android NotificationType).
TYPE_ABSENT = "absent"
TYPE_FEE_REMINDER = "fee_reminder"
TYPE_ANNOUNCEMENT = "announcement"

AUDIENCE_STUDENT = "student"
AUDIENCE_CLASS = "class"
AUDIENCE_SCHOOL = "school"


def _all_active_parents(db: Session) -> list[ParentAccount]:
    return db.execute(
        select(ParentAccount).where(ParentAccount.is_active.is_(True))
    ).scalars().all()


def _parents_for_student(db: Session, student: Student) -> list[ParentAccount]:
    mobiles = find_parent_mobiles_for_student(db, student)
    if not mobiles:
        return []
    return [p for p in _all_active_parents(db) if normalize_mobile(p.mobile_number) in mobiles]


def _parents_for_class(db: Session, class_name: str) -> list[ParentAccount]:
    students = db.execute(
        select(Student).where(Student.class_name == class_name, Student.status == "Active")
    ).scalars().all()
    wanted: set[str] = set()
    for s in students:
        wanted |= find_parent_mobiles_for_student(db, s)
    if not wanted:
        return []
    return [p for p in _all_active_parents(db) if normalize_mobile(p.mobile_number) in wanted]


def dispatch_notification(
    db: Session,
    *,
    notif_type: str,
    audience: str,
    title: str,
    body: str,
    student: Student | None = None,
    class_name: str | None = None,
    sent_by_user_id: int | None = None,
) -> NotificationLog:
    """Fan a notification out to the right parents and record the audit row.

    The caller commits the session; this stages the inbox rows and the log row
    but does not commit, so a send can be part of a larger transaction (e.g.
    marking attendance).
    """
    if audience == AUDIENCE_STUDENT:
        if student is None:
            raise ValueError("student is required for a student-audience notification")
        parents = _parents_for_student(db, student)
    elif audience == AUDIENCE_CLASS:
        if not class_name:
            raise ValueError("class_name is required for a class-audience notification")
        parents = _parents_for_class(db, class_name)
    elif audience == AUDIENCE_SCHOOL:
        parents = _all_active_parents(db)
    else:
        raise ValueError(f"Unknown audience: {audience}")

    student_id = student.student_id if student is not None else None

    parent_ids = [p.parent_id for p in parents]
    for pid in parent_ids:
        db.add(
            ParentNotification(
                parent_id=pid,
                student_id=student_id,
                notif_type=notif_type,
                title=title,
                body=body,
            )
        )
    db.flush()

    delivered = failed = 0
    if parent_ids:
        device_rows = db.execute(
            select(ParentDevice).where(
                ParentDevice.parent_id.in_(parent_ids),
                ParentDevice.is_active.is_(True),
            )
        ).scalars().all()
        tokens = [d.fcm_token for d in device_rows]
        data = {"type": notif_type}
        if student_id is not None:
            data["student_id"] = str(student_id)
        delivered, failed, invalid = firebase_service.send_to_tokens(
            tokens, title=title, body=body, data=data
        )
        if invalid:
            invalid_set = set(invalid)
            for d in device_rows:
                if d.fcm_token in invalid_set:
                    d.is_active = False

    log = NotificationLog(
        notif_type=notif_type,
        audience=audience,
        title=title,
        body=body,
        student_id=student_id,
        class_name=class_name,
        sent_by_user_id=sent_by_user_id,
        recipients_count=len(parent_ids),
        delivered_count=delivered,
        failed_count=failed,
    )
    db.add(log)
    db.flush()
    return log
