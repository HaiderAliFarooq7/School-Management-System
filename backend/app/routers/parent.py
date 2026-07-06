"""Parent-app API (multi-tenant).

Login is by mobile number: the master ``parent_directory`` routes the number to
its school, then the password is verified against that school's own
``parent_account`` table (the tenant DB). The issued JWT carries a signed
``school_id`` claim, so every subsequent request is pinned by ``get_db`` to that
same school database — parents get the exact same physical tenant isolation as
staff.

A parent may only ever read their own children's data — every per-student
endpoint re-checks the child is linked to the caller's mobile number, within
the caller's school.

Paths and JSON field names match the Android app's Retrofit interface
(``BfhsApiService``) and DTOs exactly.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.master import get_master_db
from app.db.session import get_db
from app.db.tenants import default_school_id, school_info, tenant_session
from app.deps import CurrentParent, get_current_parent
from app.models.attendance import AttendanceRecord
from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.parent_account import ParentAccount
from app.models.parent_device import ParentDevice
from app.models.parent_notification import ParentNotification
from app.models.school import School
from app.models.student import Student
from app.schemas.parent_app import (
    AttendanceRecordOut,
    AttendanceResponse,
    ExtraChargeOut,
    FeeResponse,
    MonthlyFeeOut,
    NotificationOut,
    ParentStudentOut,
    SchoolProfileOut,
)
from app.schemas.parent_auth import (
    DeviceRegisterRequest,
    ParentChangePasswordRequest,
    ParentLoginRequest,
    ParentTokenResponse,
)
from app.services import parent_directory
from app.services.parent_auth_service import (
    create_parent_access_token,
    hash_password,
    verify_password,
)
from app.services.parent_linking import find_students_for_mobile, normalize_mobile

router = APIRouter(prefix="/api/parent", tags=["parent"])


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _fmt_date(d: date) -> str:
    # "Thu, 2 Jul 2026" — built manually so it works cross-platform (no %-d).
    return f"{d:%a}, {d.day} {d:%b %Y}"


def _linked_students(db: Session, parent: CurrentParent) -> list[Student]:
    return find_students_for_mobile(db, parent.mobile_number)


def _require_own_student(db: Session, parent: CurrentParent, student_id: int) -> Student:
    for s in _linked_students(db, parent):
        if s.student_id == student_id:
            return s
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found for this parent")


def _student_remaining_dues(db: Session, student_id: int) -> int:
    vouchers = db.execute(
        select(FeeVoucher).where(FeeVoucher.student_id == student_id)
    ).scalars().all()
    charges = db.execute(
        select(ExtraCharge).where(ExtraCharge.student_id == student_id)
    ).scalars().all()
    total = sum(v.remaining for v in vouchers) + sum(float(c.remaining_amount) for c in charges)
    return int(round(total))


def _today_attendance(db: Session, student_id: int) -> str:
    rec = db.execute(
        select(AttendanceRecord.status).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date == date.today(),
        )
    ).scalars().first()
    return rec or ""


def _monthly_attendance_percent(db: Session, student_id: int) -> int:
    today = date.today()
    first = today.replace(day=1)
    rows = db.execute(
        select(AttendanceRecord.status).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date >= first,
            AttendanceRecord.attendance_date <= today,
        )
    ).scalars().all()
    if not rows:
        return 0
    present = sum(1 for r in rows if r in ("Present", "Late"))
    return int(round(present / len(rows) * 100))


def _to_student_out(db: Session, s: Student) -> ParentStudentOut:
    return ParentStudentOut(
        id=str(s.student_id),
        name=s.name,
        registration_number=s.registration_no,
        class_name=s.class_name,
        father_name=s.father_name,
        today_attendance=_today_attendance(db, s.student_id),
        remaining_dues=_student_remaining_dues(db, s.student_id),
        monthly_attendance_percent=_monthly_attendance_percent(db, s.student_id),
    )


# --------------------------------------------------------------------------- #
# Auth (tenant routing happens here)
# --------------------------------------------------------------------------- #

@router.post("/login", response_model=ParentTokenResponse)
def parent_login(payload: ParentLoginRequest, mdb: Session = Depends(get_master_db)):
    # 1. Route the mobile number to its school via the master directory, with a
    #    fallback to the default school for numbers not yet in the directory
    #    (e.g. before the first admin sync) — a successful login self-heals it.
    school_id = parent_directory.lookup_school_id(mdb, payload.mobile_number)
    from_directory = school_id is not None
    if school_id is None:
        school_id = default_school_id()
    if school_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid mobile number or password")

    info = school_info(school_id)
    if info is None or info["status"] != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid mobile number or password")

    # 2. Verify the password against that school's own parent_account table.
    core = normalize_mobile(payload.mobile_number)
    db = tenant_session(school_id)
    try:
        parent = db.execute(
            select(ParentAccount).where(ParentAccount.mobile_number == payload.mobile_number)
        ).scalar_one_or_none()
        if parent is None and core:
            for candidate in db.execute(select(ParentAccount)).scalars().all():
                if normalize_mobile(candidate.mobile_number) == core:
                    parent = candidate
                    break

        if (
            parent is None
            or not parent.is_active
            or not verify_password(payload.password, parent.password_hash)
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid mobile number or password")

        parent.last_login_at = datetime.now(timezone.utc)
        db.commit()
        parent_id = parent.parent_id
        parent_name = parent.full_name
        must_change = parent.must_change_password
        stored_mobile = parent.mobile_number
    finally:
        db.close()

    # 3. Self-heal the routing directory for accounts that logged in via the
    #    default-school fallback.
    if not from_directory:
        parent_directory.upsert(mdb, stored_mobile, school_id)
        mdb.commit()

    token = create_parent_access_token(
        parent_id=parent_id, mobile_number=stored_mobile, school_id=school_id
    )
    return ParentTokenResponse(
        access_token=token,
        parent_name=parent_name,
        mobile_number=stored_mobile,
        must_change_password=must_change,
    )


@router.post("/change-password")
def parent_change_password(
    payload: ParentChangePasswordRequest,
    parent: CurrentParent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    account = db.get(ParentAccount, parent.parent_id)
    if account is None or not verify_password(payload.current_password, account.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    account.password_hash = hash_password(payload.new_password)
    account.must_change_password = False
    db.commit()
    return {"detail": "Password changed successfully."}


@router.post("/fcm-token")
def register_fcm_token(
    payload: DeviceRegisterRequest,
    parent: CurrentParent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """Idempotent device registration. If the token already exists it's
    re-pointed at the current parent and reactivated; otherwise created."""
    existing = db.execute(
        select(ParentDevice).where(ParentDevice.fcm_token == payload.fcm_token)
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if existing:
        existing.parent_id = parent.parent_id
        existing.platform = payload.platform
        existing.is_active = True
        existing.last_seen_at = now
    else:
        db.add(
            ParentDevice(
                parent_id=parent.parent_id,
                fcm_token=payload.fcm_token,
                platform=payload.platform,
            )
        )
    db.commit()
    return {"detail": "Device registered."}


# --------------------------------------------------------------------------- #
# Data (all tenant-scoped via the token's school_id claim)
# --------------------------------------------------------------------------- #

@router.get("/students", response_model=list[ParentStudentOut])
def get_students(
    parent: CurrentParent = Depends(get_current_parent), db: Session = Depends(get_db)
):
    return [_to_student_out(db, s) for s in _linked_students(db, parent)]


@router.get("/students/{student_id}/attendance", response_model=AttendanceResponse)
def get_attendance(
    student_id: int,
    parent: CurrentParent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    _require_own_student(db, parent, student_id)
    today = date.today()
    first = today.replace(day=1)
    records = db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date >= first,
            AttendanceRecord.attendance_date <= today,
        )
        .order_by(AttendanceRecord.attendance_date.desc())
    ).scalars().all()

    present = sum(1 for r in records if r.status in ("Present", "Late"))
    absent = sum(1 for r in records if r.status == "Absent")
    leave = sum(1 for r in records if r.status == "Leave")
    total = len(records)
    overall = int(round(present / total * 100)) if total else 0

    return AttendanceResponse(
        month=f"{today:%B %Y}",
        present_count=present,
        absent_count=absent,
        leave_count=leave,
        overall_percent=overall,
        records=[
            AttendanceRecordOut(date=_fmt_date(r.attendance_date), status=r.status)
            for r in records
        ],
    )


@router.get("/students/{student_id}/fees", response_model=FeeResponse)
def get_fees(
    student_id: int,
    parent: CurrentParent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """Parents only ever need to know what's still owed — fully paid months
    are never returned here (there is nothing actionable in them), and the
    amount shown is always the remaining/pending balance, never the
    voucher's original total (a Partial voucher's total is misleading once
    part of it has been paid)."""
    _require_own_student(db, parent, student_id)
    vouchers = db.execute(
        select(FeeVoucher)
        .where(FeeVoucher.student_id == student_id, FeeVoucher.status != "Paid")
        .order_by(FeeVoucher.fee_month_sort.desc())
    ).scalars().all()

    current: MonthlyFeeOut | None = None
    history: list[MonthlyFeeOut] = []
    for v in vouchers:
        entry = MonthlyFeeOut(
            month=v.fee_month, amount=int(round(v.remaining)), status="Unpaid", due_date=None
        )
        if current is None:
            current = entry
        else:
            history.append(entry)
    return FeeResponse(current=current, history=history)


@router.get("/students/{student_id}/extra-charges", response_model=list[ExtraChargeOut])
def get_extra_charges(
    student_id: int,
    parent: CurrentParent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """Only charges still owed are shown — same reasoning as fees above."""
    _require_own_student(db, parent, student_id)
    charges = db.execute(
        select(ExtraCharge)
        .where(ExtraCharge.student_id == student_id, ExtraCharge.status != "Paid")
        .order_by(ExtraCharge.created_at.desc())
    ).scalars().all()
    out = []
    for c in charges:
        if float(c.remaining_amount) <= 0:
            continue
        label = f"Due {c.created_at:%d %b %Y}" if c.created_at else "Due"
        out.append(
            ExtraChargeOut(
                id=str(c.charge_id),
                title=c.description,
                amount=int(round(float(c.remaining_amount))),
                date_label=label,
                status="Unpaid",
            )
        )
    return out


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    parent: CurrentParent = Depends(get_current_parent), db: Session = Depends(get_db)
):
    rows = db.execute(
        select(ParentNotification)
        .where(ParentNotification.parent_id == parent.parent_id)
        .order_by(ParentNotification.created_at.desc())
        .limit(100)
    ).scalars().all()
    return [
        NotificationOut(
            id=str(n.id),
            title=n.title,
            body=n.body,
            time_label=_notification_time_label(n.created_at),
            unread=not n.is_read,
            type=n.notif_type,
            student_id=str(n.student_id) if n.student_id is not None else None,
        )
        for n in rows
    ]


@router.post("/notifications/read")
def mark_notifications_read(
    parent: CurrentParent = Depends(get_current_parent), db: Session = Depends(get_db)
):
    db.query(ParentNotification).filter(
        ParentNotification.parent_id == parent.parent_id,
        ParentNotification.is_read.is_(False),
    ).update({ParentNotification.is_read: True})
    db.commit()
    return {"detail": "Marked read."}


@router.get("/school", response_model=SchoolProfileOut)
def get_school_profile(
    parent: CurrentParent = Depends(get_current_parent), db: Session = Depends(get_db)
):
    school = db.execute(select(School)).scalars().first()
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School profile not configured")
    # The parent app's profile screen shows a few fields the core School model
    # doesn't store yet (tagline, principal, established, email, website, about);
    # return what exists and empty strings for the rest until School is extended.
    return SchoolProfileOut(
        name=school.name or "",
        tagline="",
        principal="",
        established="",
        phone=school.phone or "",
        email="",
        address=school.address or "",
        website="",
        about="",
    )


def _notification_time_label(created_at: datetime) -> str:
    """Compact relative label for the WhatsApp-style list: time-of-day today,
    'Yesterday', 'N days ago', else a date."""
    if created_at is None:
        return ""
    now = datetime.now(timezone.utc)
    ts = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    delta_days = (now.date() - ts.date()).days
    if delta_days <= 0:
        return f"{ts:%I:%M %p}".lstrip("0")
    if delta_days == 1:
        return "Yesterday"
    if delta_days < 7:
        return f"{delta_days} days ago"
    return f"{ts:%d %b %Y}"
