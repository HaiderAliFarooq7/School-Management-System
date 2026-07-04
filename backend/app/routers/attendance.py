from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role, scope_class_filter
from app.logging_config import logger
from app.models.attendance import AttendanceRecord
from app.models.grade import Grade
from app.models.student import Student
from app.schemas.attendance import (
    AbsentTodayRow,
    AttendanceDailyStatusRow,
    AttendanceOut,
    AttendanceSummaryRow,
    MarkAttendanceRequest,
)
from app.services import notification_service

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _notify_absent_parents(db: Session, newly_absent_student_ids: list[int]) -> None:
    """Fire an 'absent' push + inbox notification to each affected student's
    parents (within this school's tenant session). Best-effort: any failure
    here must never fail attendance marking, so it runs after the attendance
    commit and swallows its own errors."""
    for student_id in newly_absent_student_ids:
        try:
            student = db.get(Student, student_id)
            if student is None:
                continue
            notification_service.dispatch_notification(
                db,
                notif_type=notification_service.TYPE_ABSENT,
                audience=notification_service.AUDIENCE_STUDENT,
                title="Attendance Alert",
                body=f"{student.name} was marked absent today.",
                student=student,
            )
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            logger.exception("Failed to send absent notification for student %s", student_id)


@router.post("/mark", response_model=list[AttendanceOut], dependencies=[Depends(require_role("Admin", "Teacher"))])
def mark_attendance(
    payload: MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Teachers can only ever mark their own assigned class, and only students
    # who actually belong to that class — otherwise a Teacher token could
    # write attendance for any student in the school.
    scope_class_filter(current_user, payload.class_name)
    class_student_ids = set(
        db.execute(
            select(Student.student_id).where(Student.class_name == payload.class_name)
        ).scalars().all()
    )
    outside_class = [e.student_id for e in payload.entries if e.student_id not in class_student_ids]
    if outside_class:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{len(outside_class)} student(s) in this request are not enrolled in {payload.class_name}.",
        )
    existing_by_student = {
        r.student_id: r
        for r in db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id.in_([e.student_id for e in payload.entries]),
                AttendanceRecord.attendance_date == payload.attendance_date,
                AttendanceRecord.period_name == payload.period_name,
            )
        ).scalars().all()
    } if payload.entries else {}

    results = []
    newly_absent: list[int] = []
    is_today = payload.attendance_date == date_type.today()
    for entry in payload.entries:
        existing = existing_by_student.get(entry.student_id)
        if existing:
            # Only notify when a record newly becomes Absent (not on re-saves of
            # an already-absent record), to avoid duplicate parent alerts.
            if entry.status == "Absent" and existing.status != "Absent" and is_today:
                newly_absent.append(entry.student_id)
            existing.status = entry.status
            existing.remarks = entry.remarks
            existing.marked_by_user_id = current_user.user_id
            results.append(existing)
        else:
            if entry.status == "Absent" and is_today:
                newly_absent.append(entry.student_id)
            record = AttendanceRecord(
                student_id=entry.student_id,
                class_name=payload.class_name,
                attendance_date=payload.attendance_date,
                period_name=payload.period_name,
                status=entry.status,
                remarks=entry.remarks,
                marked_by_user_id=current_user.user_id,
            )
            db.add(record)
            results.append(record)
    db.commit()

    # Automatic absent notifications — after the attendance commit, best-effort.
    if newly_absent:
        _notify_absent_parents(db, newly_absent)
        for r in results:
            db.refresh(r)
    return results


@router.get("", response_model=list[AttendanceOut])
def get_attendance_for_class_date(
    class_name: str,
    attendance_date: date_type,
    period_name: str = "Full Day",
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    class_name = scope_class_filter(current_user, class_name)
    return db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.class_name == class_name,
            AttendanceRecord.attendance_date == attendance_date,
            AttendanceRecord.period_name == period_name,
        )
    ).scalars().all()


@router.get("/summary", response_model=list[AttendanceSummaryRow])
def get_attendance_summary(
    class_name: str,
    date_from: date_type,
    date_to: date_type,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    class_name = scope_class_filter(current_user, class_name)
    students = db.execute(
        select(Student).where(Student.class_name == class_name, Student.status == "Active")
    ).scalars().all()

    # Status counts for every student in the class, in one grouped query.
    counts: dict[int, dict[str, int]] = {}
    if students:
        for sid, record_status, n in db.execute(
            select(AttendanceRecord.student_id, AttendanceRecord.status, func.count())
            .where(
                AttendanceRecord.student_id.in_([s.student_id for s in students]),
                AttendanceRecord.attendance_date >= date_from,
                AttendanceRecord.attendance_date <= date_to,
            )
            .group_by(AttendanceRecord.student_id, AttendanceRecord.status)
        ).all():
            counts.setdefault(sid, {})[record_status] = n

    rows = []
    for s in students:
        by_status = counts.get(s.student_id, {})
        present = by_status.get("Present", 0)
        absent = by_status.get("Absent", 0)
        late = by_status.get("Late", 0)
        leave = by_status.get("Leave", 0)
        total = sum(by_status.values())
        rows.append(
            AttendanceSummaryRow(
                student_id=s.student_id,
                registration_no=s.registration_no,
                name=s.name,
                present=present,
                absent=absent,
                late=late,
                leave=leave,
                total_marked=total,
                pct_present=(present / total * 100) if total > 0 else 0,
            )
        )
    return rows


@router.get("/daily-status", response_model=list[AttendanceDailyStatusRow], dependencies=[Depends(require_role("Admin", "Accountant"))])
def get_attendance_daily_status(attendance_date: date_type | None = None, db: Session = Depends(get_db)):
    """For Admin/Accountant: which classes have (and haven't) marked
    attendance for a given day (default today) — so the office can chase up
    teachers or notify parents before the day is over. Classes with no
    active students are omitted."""
    target_date = attendance_date or date_type.today()
    grades = db.execute(select(Grade).order_by(Grade.class_name)).scalars().all()

    active_by_class = dict(
        db.execute(
            select(Student.class_name, func.count(Student.student_id))
            .where(Student.status == "Active")
            .group_by(Student.class_name)
        ).all()
    )
    marked_by_class = dict(
        db.execute(
            select(AttendanceRecord.class_name, func.count(func.distinct(AttendanceRecord.student_id)))
            .where(AttendanceRecord.attendance_date == target_date)
            .group_by(AttendanceRecord.class_name)
        ).all()
    )

    rows = []
    for g in grades:
        total_active = active_by_class.get(g.class_name, 0)
        if total_active == 0:
            continue
        marked_count = marked_by_class.get(g.class_name, 0)
        rows.append(
            AttendanceDailyStatusRow(
                class_name=g.class_name,
                total_active_students=total_active,
                marked_count=marked_count,
                fully_marked=marked_count >= total_active,
                any_marked=marked_count > 0,
            )
        )
    return rows


@router.get("/absent-today", response_model=list[AbsentTodayRow])
def get_absent_today(
    attendance_date: date_type | None = None,
    class_name: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Students with at least one Absent record for the given day (default
    today). Teachers only ever see their own assigned class."""
    target_date = attendance_date or date_type.today()
    effective_class = scope_class_filter(current_user, class_name)

    query = (
        select(Student)
        .join(AttendanceRecord, AttendanceRecord.student_id == Student.student_id)
        .where(AttendanceRecord.attendance_date == target_date, AttendanceRecord.status == "Absent")
        .distinct()
    )
    if effective_class:
        query = query.where(Student.class_name == effective_class)
    students = db.execute(query).scalars().all()
    return [
        AbsentTodayRow(
            student_id=s.student_id, registration_no=s.registration_no, name=s.name,
            father_name=s.father_name, class_name=s.class_name, phone=s.phone,
        )
        for s in students
    ]


@router.get("/student/{student_id}", response_model=list[AttendanceOut])
def get_student_attendance_history(
    student_id: int,
    date_from: date_type,
    date_to: date_type,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    scope_class_filter(current_user, student.class_name)
    return db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date >= date_from,
            AttendanceRecord.attendance_date <= date_to,
        )
        .order_by(AttendanceRecord.attendance_date.desc())
    ).scalars().all()
