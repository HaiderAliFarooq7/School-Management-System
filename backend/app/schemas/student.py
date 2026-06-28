from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    father_name: str = Field(min_length=1, max_length=150)
    class_name: str = Field(min_length=1, max_length=50)
    dob: date | None = None
    admission_date: date | None = None
    b_form: str | None = Field(default=None, max_length=50)
    cnic: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    photo_path: str | None = None
    default_fee: float | None = Field(default=None, ge=0)


class StudentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    father_name: str = Field(min_length=1, max_length=150)
    class_name: str = Field(min_length=1, max_length=50)
    dob: date | None = None
    admission_date: date | None = None
    b_form: str | None = Field(default=None, max_length=50)
    cnic: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    photo_path: str | None = None
    default_fee: float | None = Field(default=None, ge=0)
    status: str = "Active"


class StudentOut(BaseModel):
    student_id: int
    registration_no: str
    name: str
    father_name: str
    class_name: str
    dob: date | None = None
    admission_date: date | None = None
    b_form: str | None = None
    cnic: str | None = None
    phone: str | None = None
    address: str | None = None
    photo_path: str | None = None
    status: str
    default_fee: float | None = None
    fee_status: str | None = None
    total_pending: float | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentSearchParams(BaseModel):
    name: str = ""
    registration_no: str = ""
    cnic: str = ""
    phone: str = ""
    father_name: str = ""
    address: str = ""
    class_filter: str = ""
    status_filter: str = ""
    admission_year: str = ""
    dob_from: str = ""
    dob_to: str = ""
    fee_status_filter: str = ""
