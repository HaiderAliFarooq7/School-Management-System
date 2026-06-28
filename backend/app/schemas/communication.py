from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderOut(BaseModel):
    id: int
    name: str
    type: str
    enabled: bool
    configuration_json: dict
    business_name: str | None = None
    phone_number_display: str | None = None
    api_version: str | None = None
    last_tested_at: datetime | None = None
    last_test_status: str | None = None
    last_error: str | None = None
    messages_sent_today: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    configuration_json: dict | None = None


class WhatsAppTestConnectionResult(BaseModel):
    status: str  # "connected" | "disconnected"
    business_name: str | None = None
    phone_number: str | None = None
    api_version: str | None = None
    quality_rating: str | None = None
    error: str | None = None


class WhatsAppTestMessageRequest(BaseModel):
    recipient: str
    template_name: str = "hello_world"
    language_code: str = "en_US"


class WhatsAppTestMessageResult(BaseModel):
    status: str  # "sent" | "failed"
    message_id: str | None = None
    http_status: int | None = None
    error: str | None = None
    provider_response: dict | None = None


class TemplateOut(BaseModel):
    id: int
    name: str
    type: str
    message: str
    variables: list[str]
    enabled: bool
    whatsapp_template_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateUpdate(BaseModel):
    message: str | None = None
    variables: list[str] | None = None
    enabled: bool | None = None
    whatsapp_template_name: str | None = None


class QueueCreate(BaseModel):
    student_id: int | None = None
    recipient_name: str | None = None
    provider_type: str  # "sms" | "whatsapp"
    notification_type: str  # "custom" | "attendance_absent" | "fee_reminder"
    recipient: str
    message: str


class QueueOut(BaseModel):
    id: int
    student_id: int | None
    recipient_name: str | None
    provider_type: str
    notification_type: str
    recipient: str
    message: str
    status: str
    retry_count: int
    scheduled_at: datetime | None
    sent_at: datetime | None
    error_message: str | None
    provider_response: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoryOut(BaseModel):
    log_id: int
    student_id: int | None
    provider: str | None
    recipient: str | None
    notification_type: str
    message: str | None
    status: str
    response: str | None
    error: str | None
    template: str | None = None
    meta_message_id: str | None = None
    http_status: int | None = None
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestProviderRequest(BaseModel):
    provider_id: int


class WhatsAppAccountOut(BaseModel):
    id: int
    name: str
    business_account_id: str | None = None
    phone_number_id: str | None = None
    graph_version: str | None = None
    use_templates: bool
    enabled: bool
    is_default: bool
    has_access_token: bool
    has_webhook_verify_token: bool
    has_webhook_secret: bool
    business_name: str | None = None
    phone_number_display: str | None = None
    api_version: str | None = None
    last_tested_at: datetime | None = None
    last_test_status: str | None = None
    last_error: str | None = None
    messages_sent_today: int = 0
    created_at: datetime
    updated_at: datetime


class WhatsAppAccountCreate(BaseModel):
    name: str
    business_account_id: str | None = None
    phone_number_id: str
    access_token: str
    graph_version: str = "v25.0"
    use_templates: bool = False
    webhook_verify_token: str | None = None
    webhook_secret: str | None = None
    enabled: bool = True


class WhatsAppAccountUpdate(BaseModel):
    name: str | None = None
    business_account_id: str | None = None
    phone_number_id: str | None = None
    access_token: str | None = None  # blank/omitted keeps the existing encrypted token
    graph_version: str | None = None
    use_templates: bool | None = None
    webhook_verify_token: str | None = None
    webhook_secret: str | None = None
    enabled: bool | None = None


class WhatsAppAccountTestDraftRequest(BaseModel):
    access_token: str
    phone_number_id: str
    business_account_id: str | None = None
    graph_version: str = "v25.0"


class AnalyticsDayCount(BaseModel):
    day: str
    sent: int
    failed: int


class AnalyticsOut(BaseModel):
    pending: int
    processing: int
    sent_today: int
    failed_today: int
    by_day: list[AnalyticsDayCount]
