"""Schemas for the admin-side parent management & notification center."""
from datetime import datetime

from pydantic import BaseModel, Field


# --- Parent management ---

class ParentAccountOut(BaseModel):
    parent_id: int
    mobile_number: str
    full_name: str | None
    is_active: bool
    must_change_password: bool
    device_count: int
    student_count: int
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class ParentCreateRequest(BaseModel):
    mobile_number: str = Field(min_length=6, max_length=20)
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class ParentUpdateRequest(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class ParentResetPasswordResponse(BaseModel):
    detail: str


class ParentSyncResponse(BaseModel):
    created: int
    skipped: int
    detail: str


# --- Device management ---

class ParentDeviceOut(BaseModel):
    device_id: int
    parent_id: int
    platform: str
    is_active: bool
    created_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


# --- Notification center ---

class SendNotificationRequest(BaseModel):
    notif_type: str = Field(pattern="^(absent|fee_reminder|announcement)$")
    audience: str = Field(pattern="^(student|class|school)$")
    title: str = Field(min_length=1, max_length=150)
    body: str = Field(min_length=1, max_length=2000)
    student_id: int | None = None
    class_name: str | None = None


class NotifSettingsOut(BaseModel):
    auto_notify_absent: bool


class NotifSettingsUpdate(BaseModel):
    auto_notify_absent: bool


class AbsentAllResponse(BaseModel):
    notified: int
    detail: str


class NotificationLogOut(BaseModel):
    log_id: int
    notif_type: str
    audience: str
    title: str
    body: str
    student_id: int | None
    class_name: str | None
    sent_by_user_id: int | None
    recipients_count: int
    delivered_count: int
    failed_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
