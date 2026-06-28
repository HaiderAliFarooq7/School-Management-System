from pydantic import BaseModel, ConfigDict


class SchoolUpdate(BaseModel):
    name: str
    address: str
    phone: str
    logo_path: str | None = None
    bank_name: str
    account_title: str
    account_number: str
    iban: str
    fee_due_day: int = 10
    challan_note: str | None = None


class NotificationSettingsUpdate(BaseModel):
    sms_enabled: bool = False
    sms_gateway: str = ""
    sms_api_key: str = ""
    sms_api_secret: str = ""
    sms_sender_id: str = ""
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_password: str = ""


class CommunicationSettingsUpdate(BaseModel):
    """Attendance auto-notify flag for the Communication Module — separate
    endpoint from the legacy notification-settings (sms/email gateway
    credentials) above."""

    auto_notify_absent: bool = False


class SchoolOut(SchoolUpdate, NotificationSettingsUpdate, CommunicationSettingsUpdate):
    school_id: int

    model_config = ConfigDict(from_attributes=True)
