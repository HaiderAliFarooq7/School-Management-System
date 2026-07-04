"""Response schemas for the parent app. Field names match the Android DTOs
(``com.bfhs.parent.data.network.dto``) exactly so the two sides stay in sync."""
from pydantic import BaseModel


class ParentStudentOut(BaseModel):
    id: str
    name: str
    registration_number: str
    class_name: str
    father_name: str
    today_attendance: str          # Present | Absent | Leave | ""
    remaining_dues: int
    monthly_attendance_percent: int


class AttendanceRecordOut(BaseModel):
    date: str                      # display form, e.g. "Thu, 2 Jul 2026"
    status: str


class AttendanceResponse(BaseModel):
    month: str
    present_count: int
    absent_count: int
    leave_count: int
    overall_percent: int
    records: list[AttendanceRecordOut]


class MonthlyFeeOut(BaseModel):
    month: str
    amount: int
    status: str                    # Paid | Unpaid
    due_date: str | None = None


class FeeResponse(BaseModel):
    current: MonthlyFeeOut | None = None
    history: list[MonthlyFeeOut]


class ExtraChargeOut(BaseModel):
    id: str
    title: str
    amount: int
    date_label: str
    status: str                    # Paid | Unpaid


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    time_label: str
    unread: bool
    type: str                      # absent | fee_reminder | announcement
    student_id: str | None = None


class SchoolProfileOut(BaseModel):
    name: str
    tagline: str
    principal: str
    established: str
    phone: str
    email: str
    address: str
    website: str
    about: str
