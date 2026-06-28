from typing import Any, Literal

from pydantic import BaseModel

ImportMode = Literal["delete_all", "update_or_add", "new_only"]

IMPORT_FIELDS: dict[str, str] = {
    "registration_no": "Registration Number",
    "name": "Student Name",
    "father_name": "Father's Name",
    "class_name": "Class",
    "phone": "Parent Phone",
    "cnic": "CNIC",
    "default_fee": "Monthly Fee",
    "dob": "Date of Birth",
    "admission_date": "Admission Date",
    "b_form": "B-Form Number",
    "address": "Address",
    "status": "Status",
}


class AnalyzeResponse(BaseModel):
    columns: list[str]
    suggested_mapping: dict[str, str | None]
    available_fields: dict[str, str] = IMPORT_FIELDS
    raw_rows: list[dict[str, Any]]
    total_rows: int
    distinct_class_values: list[str]
    suggested_class_mapping: dict[str, str | None]
    known_classes: list[str]


class PreviewRequest(BaseModel):
    raw_rows: list[dict[str, Any]]
    mapping: dict[str, str | None]  # excel column -> our field key (None = ignore this column)
    class_value_mapping: dict[str, str]  # raw class value -> canonical class_name
    import_mode: ImportMode


class PreviewRow(BaseModel):
    row_number: int
    data: dict[str, Any]
    status: Literal["valid", "invalid", "duplicate"]
    errors: list[str] = []
    missing_fields: list[str] = []


class PreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    missing_fields_rows: int
    rows: list[PreviewRow]


class ExecuteRequest(BaseModel):
    raw_rows: list[dict[str, Any]]
    mapping: dict[str, str | None]
    class_value_mapping: dict[str, str]
    import_mode: ImportMode
    only_valid_rows: bool = True
    confirm_delete_all: bool = False


class ExecuteError(BaseModel):
    row_number: int
    reason: str


class ExecuteResult(BaseModel):
    imported: int
    updated: int
    skipped: int
    failed: int
    errors: list[ExecuteError]
