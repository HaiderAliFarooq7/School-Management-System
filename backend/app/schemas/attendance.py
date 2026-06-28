from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AttendanceEntry(BaseModel):
    student_id: int
    status: str  # Present | Absent | Late | Leave
    remarks: str | None = None


class MarkAttendanceRequest(BaseModel):
    class_name: str
    attendance_date: date
    period_name: str = "Full Day"
    entries: list[AttendanceEntry]


class AttendanceOut(BaseModel):
    attendance_id: int
    student_id: int
    class_name: str
    attendance_date: date
    period_name: str
    status: str
    remarks: str | None = None
    marked_by_user_id: int | None = None
    marked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceSummaryRow(BaseModel):
    student_id: int
    registration_no: str
    name: str
    present: int
    absent: int
    late: int
    leave: int
    total_marked: int
    pct_present: float


class AttendanceDailyStatusRow(BaseModel):
    class_name: str
    total_active_students: int
    marked_count: int
    fully_marked: bool
    any_marked: bool


class AbsentTodayRow(BaseModel):
    student_id: int
    registration_no: str
    name: str
    father_name: str
    class_name: str
    phone: str | None
