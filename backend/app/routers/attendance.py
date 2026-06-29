from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role, scope_class_filter
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

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/mark", response_model=list[AttendanceOut], dependencies=[Depends(require_role("Admin", "Teacher"))])
def mark_attendance(
    payload: MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    results = []
    for entry in payload.entries:
        existing = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id == entry.student_id,
                AttendanceRecord.attendance_date == payload.attendance_date,
                AttendanceRecord.period_name == payload.period_name,
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = entry.status
            existing.remarks = entry.remarks
            existing.marked_by_user_id = current_user.user_id
            results.append(existing)
        else:
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
    return results


@router.get("", response_model=list[AttendanceOut])
def get_attendance_for_class_date(
    class_name: str,
    attendance_date: date_type,
    period_name: str = "Full Day",
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
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
    students = db.execute(
        select(Student).where(Student.class_name == class_name, Student.status == "Active")
    ).scalars().all()

    rows = []
    for s in students:
        records = db.execute(
            select(AttendanceRecord.status).where(
                AttendanceRecord.student_id == s.student_id,
                AttendanceRecord.attendance_date >= date_from,
                AttendanceRecord.attendance_date <= date_to,
            )
        ).scalars().all()
        present = sum(1 for r in records if r == "Present")
        absent = sum(1 for r in records if r == "Absent")
        late = sum(1 for r in records if r == "Late")
        leave = sum(1 for r in records if r == "Leave")
        total = len(records)
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

    rows = []
    for g in grades:
        total_active = db.execute(
            select(func.count(Student.student_id)).where(Student.class_name == g.class_name, Student.status == "Active")
        ).scalar_one()
        if total_active == 0:
            continue
        marked_count = db.execute(
            select(func.count(func.distinct(AttendanceRecord.student_id))).where(
                AttendanceRecord.class_name == g.class_name, AttendanceRecord.attendance_date == target_date,
            )
        ).scalar_one()
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
    return db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.attendance_date >= date_from,
            AttendanceRecord.attendance_date <= date_to,
        )
        .order_by(AttendanceRecord.attendance_date.desc())
    ).scalars().all()
