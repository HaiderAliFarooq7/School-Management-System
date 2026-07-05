"""Admin/office-facing parent module: parent management, device management,
the notification center (manual sends), and notification history.

Every endpoint operates on the signed-in staff member's OWN school (tenant)
database via ``get_db`` — an Admin only ever sees and manages their school's
parents, so multi-tenant isolation holds. Creating/syncing parent accounts also
maintains the master ``parent_directory`` (mobile -> school routing) so those
parents can log in.

Role rules (on top of the tenant staff JWT):
  * Admin       — full parent management; may send any notification type to any
                  audience (announcement, fee reminder, class, whole school).
  * Accountant  — may send fee reminders only; may view history.
  * Teacher     — no access (teachers never send notifications).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.master import get_master_db
from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.notification_log import NotificationLog
from app.models.parent_account import ParentAccount
from app.models.parent_device import ParentDevice
from app.models.school import School
from app.models.student import Student
from app.schemas.parent_admin import (
    AbsentAllResponse,
    NotifSettingsOut,
    NotifSettingsUpdate,
    NotificationLogOut,
    ParentAccountOut,
    ParentCreateRequest,
    ParentDeviceOut,
    ParentResetPasswordResponse,
    ParentSyncResponse,
    ParentUpdateRequest,
    SendNotificationRequest,
)
from app.services import notification_service, parent_directory
from app.services.parent_auth_service import hash_password
from app.services.parent_linking import find_students_for_mobile, normalize_mobile

router = APIRouter(prefix="/api/admin/parents", tags=["parent-admin"])
notif_router = APIRouter(prefix="/api/admin/notifications", tags=["parent-admin"])


# --------------------------------------------------------------------------- #
# Parent management (Admin only)
# --------------------------------------------------------------------------- #

def _to_account_out(db: Session, p: ParentAccount) -> ParentAccountOut:
    device_count = db.execute(
        select(func.count(ParentDevice.device_id)).where(
            ParentDevice.parent_id == p.parent_id, ParentDevice.is_active.is_(True)
        )
    ).scalar_one()
    student_count = len(find_students_for_mobile(db, p.mobile_number))
    return ParentAccountOut(
        parent_id=p.parent_id,
        mobile_number=p.mobile_number,
        full_name=p.full_name,
        is_active=p.is_active,
        must_change_password=p.must_change_password,
        device_count=device_count,
        student_count=student_count,
        created_at=p.created_at,
        last_login_at=p.last_login_at,
    )


@router.get("", response_model=list[ParentAccountOut])
def list_parents(
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    parents = db.execute(
        select(ParentAccount).order_by(ParentAccount.created_at.desc())
    ).scalars().all()
    return [_to_account_out(db, p) for p in parents]


@router.post("", response_model=ParentAccountOut)
def create_parent(
    payload: ParentCreateRequest,
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
    mdb: Session = Depends(get_master_db),
):
    existing = db.execute(
        select(ParentAccount).where(ParentAccount.mobile_number == payload.mobile_number)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "A parent with this mobile number already exists.")
    # Default password is the mobile number itself (bcrypt-hashed).
    raw_password = payload.password or payload.mobile_number
    parent = ParentAccount(
        mobile_number=payload.mobile_number,
        full_name=payload.full_name,
        password_hash=hash_password(raw_password),
        must_change_password=payload.password is None,
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)

    # Route this mobile number to this school in the master directory.
    if current_user.school_id is not None:
        parent_directory.upsert(mdb, payload.mobile_number, current_user.school_id)
        mdb.commit()
    return _to_account_out(db, parent)


@router.patch("/{parent_id}", response_model=ParentAccountOut)
def update_parent(
    parent_id: int,
    payload: ParentUpdateRequest,
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    parent = db.get(ParentAccount, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent not found")
    if payload.full_name is not None:
        parent.full_name = payload.full_name
    if payload.is_active is not None:
        parent.is_active = payload.is_active
    db.commit()
    db.refresh(parent)
    return _to_account_out(db, parent)


@router.post("/{parent_id}/reset-password", response_model=ParentResetPasswordResponse)
def reset_parent_password(
    parent_id: int,
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    """Reset a parent's password back to their mobile number (the default),
    flagged so they're prompted to change it on next login."""
    parent = db.get(ParentAccount, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent not found")
    parent.password_hash = hash_password(parent.mobile_number)
    parent.must_change_password = True
    db.commit()
    return ParentResetPasswordResponse(detail="Password reset to the parent's mobile number.")


@router.post("/sync", response_model=ParentSyncResponse)
def sync_parent_accounts(
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
    mdb: Session = Depends(get_master_db),
):
    """Provision a parent_account for every distinct mobile number found on
    this school's students (student.phone + phone-type student_contact rows)
    that doesn't already have one. Default password = mobile number. Also
    registers each in the master directory. Idempotent."""
    students = db.execute(select(Student)).scalars().all()

    existing_cores = {
        normalize_mobile(p.mobile_number)
        for p in db.execute(select(ParentAccount)).scalars().all()
    }

    discovered: dict[str, tuple[str, str | None]] = {}
    for s in students:
        for raw in _student_raw_mobiles(db, s):
            core = normalize_mobile(raw)
            if core and core not in discovered:
                discovered[core] = (raw.strip(), s.father_name)

    created = 0
    skipped = 0
    for core, (display, father) in discovered.items():
        if core in existing_cores:
            skipped += 1
            continue
        db.add(
            ParentAccount(
                mobile_number=display,
                full_name=father,
                password_hash=hash_password(display),
                must_change_password=True,
            )
        )
        existing_cores.add(core)
        if current_user.school_id is not None:
            parent_directory.upsert(mdb, display, current_user.school_id)
        created += 1
    db.commit()
    if current_user.school_id is not None:
        mdb.commit()
    return ParentSyncResponse(
        created=created,
        skipped=skipped,
        detail=f"Created {created} new parent account(s); {skipped} already existed.",
    )


@router.get("/{parent_id}/devices", response_model=list[ParentDeviceOut])
def list_parent_devices(
    parent_id: int,
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    if db.get(ParentAccount, parent_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent not found")
    return db.execute(
        select(ParentDevice)
        .where(ParentDevice.parent_id == parent_id)
        .order_by(ParentDevice.last_seen_at.desc())
    ).scalars().all()


@router.get("/devices/all", response_model=list[ParentDeviceOut])
def list_all_devices(
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    return db.execute(
        select(ParentDevice).order_by(ParentDevice.last_seen_at.desc())
    ).scalars().all()


def _student_raw_mobiles(db: Session, student: Student) -> list[str]:
    from app.models.student_contact import StudentContact

    values: list[str] = []
    if student.phone:
        values.append(student.phone)
    contact_values = db.execute(
        select(StudentContact.contact_value).where(
            StudentContact.student_id == student.student_id,
            StudentContact.contact_type.in_(("phone", "mobile", "whatsapp", "cell")),
        )
    ).scalars().all()
    values.extend(contact_values)
    return values


# --------------------------------------------------------------------------- #
# Notification center
# --------------------------------------------------------------------------- #

@notif_router.post("/send", response_model=NotificationLogOut)
def send_notification(
    payload: SendNotificationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manual send. Admin may send anything; Accountant may send fee reminders
    only; Teachers are forbidden."""
    role = current_user.role_name
    if role == "Teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Teachers cannot send notifications.")
    if role == "Accountant" and payload.notif_type != notification_service.TYPE_FEE_REMINDER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accountants may send fee reminders only.")
    if role not in ("Admin", "Accountant", "SuperAdmin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to send notifications.")

    student = None
    if payload.audience == notification_service.AUDIENCE_STUDENT:
        if payload.student_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "student_id is required for a student send.")
        student = db.get(Student, payload.student_id)
        if student is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    elif payload.audience == notification_service.AUDIENCE_CLASS and not payload.class_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "class_name is required for a class send.")

    log = notification_service.dispatch_notification(
        db,
        notif_type=payload.notif_type,
        audience=payload.audience,
        title=payload.title,
        body=payload.body,
        student=student,
        class_name=payload.class_name,
        sent_by_user_id=current_user.user_id if not current_user.is_super else None,
    )
    db.commit()
    db.refresh(log)
    return log


@notif_router.get("/log", response_model=list[NotificationLogOut])
def notification_history(
    limit: int = 100,
    current_user: CurrentUser = Depends(require_role("Admin", "Accountant")),
    db: Session = Depends(get_db),
):
    return db.execute(
        select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(min(limit, 500))
    ).scalars().all()


@notif_router.get("/settings", response_model=NotifSettingsOut)
def get_notification_settings(
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    school = db.execute(select(School).limit(1)).scalar_one_or_none()
    return NotifSettingsOut(auto_notify_absent=school is None or school.auto_notify_absent)


@notif_router.put("/settings", response_model=NotifSettingsOut)
def update_notification_settings(
    payload: NotifSettingsUpdate,
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    school = db.execute(select(School).limit(1)).scalar_one_or_none()
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School profile not configured")
    school.auto_notify_absent = payload.auto_notify_absent
    db.commit()
    return NotifSettingsOut(auto_notify_absent=school.auto_notify_absent)


@notif_router.post("/absent-all", response_model=AbsentAllResponse)
def notify_all_absentees(
    current_user: CurrentUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    """Send an absent alert to the parents of every student marked Absent today
    (this school). Useful when auto-notify is off, or to re-send in one click."""
    count = notification_service.notify_all_absentees(
        db, sent_by_user_id=current_user.user_id if not current_user.is_super else None
    )
    db.commit()
    return AbsentAllResponse(
        notified=count, detail=f"Sent absent alerts for {count} student(s) marked absent today."
    )
