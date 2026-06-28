from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.logging_config import logger
from app.models.communication_provider import CommunicationProvider
from app.models.notification_log import NotificationLog
from app.models.notification_queue import NotificationQueue
from app.models.notification_template import NotificationTemplate
from app.models.student import Student
from app.schemas.communication import (
    AnalyticsDayCount,
    AnalyticsOut,
    HistoryOut,
    ProviderOut,
    ProviderUpdate,
    QueueCreate,
    QueueOut,
    TemplateOut,
    TemplateUpdate,
    TestProviderRequest,
    WhatsAppAccountCreate,
    WhatsAppAccountOut,
    WhatsAppAccountTestDraftRequest,
    WhatsAppAccountUpdate,
    WhatsAppTestConnectionResult,
    WhatsAppTestMessageRequest,
    WhatsAppTestMessageResult,
)
from app.services.crypto import encrypt
from app.services.notification_service import queue_notification, test_provider
from app.services.providers import WhatsAppCloudProvider

router = APIRouter(
    prefix="/api/communication",
    tags=["communication"],
    dependencies=[Depends(get_current_user)],
)


def _messages_sent_today(db: Session, provider_type: str) -> int:
    today_start = datetime.combine(date.today(), datetime.min.time())
    return db.execute(
        select(func.count()).select_from(NotificationLog).where(
            NotificationLog.provider == provider_type,
            NotificationLog.status == "sent",
            NotificationLog.created_at >= today_start,
        )
    ).scalar_one()


def _to_provider_out(db: Session, provider: CommunicationProvider) -> ProviderOut:
    return ProviderOut(
        **{
            "id": provider.id, "name": provider.name, "type": provider.type, "enabled": provider.enabled,
            "configuration_json": provider.configuration_json, "business_name": provider.business_name,
            "phone_number_display": provider.phone_number_display, "api_version": provider.api_version,
            "last_tested_at": provider.last_tested_at, "last_test_status": provider.last_test_status,
            "last_error": provider.last_error, "created_at": provider.created_at, "updated_at": provider.updated_at,
            "messages_sent_today": _messages_sent_today(db, provider.type),
        }
    )


@router.get("/providers", response_model=list[ProviderOut], dependencies=[Depends(require_role("Admin"))])
def list_providers(db: Session = Depends(get_db)):
    """WhatsApp accounts have their own dedicated CRUD below (multi-account) —
    this generic list/update pair is now only for single-instance provider
    placeholders like Android Gateway."""
    providers = db.execute(
        select(CommunicationProvider)
        .where(CommunicationProvider.type != "whatsapp_cloud")
        .order_by(CommunicationProvider.id)
    ).scalars().all()
    return [_to_provider_out(db, p) for p in providers]


@router.put("/providers/{provider_id}", response_model=ProviderOut, dependencies=[Depends(require_role("Admin"))])
def update_provider(provider_id: int, payload: ProviderUpdate, db: Session = Depends(get_db)):
    provider = db.get(CommunicationProvider, provider_id)
    if provider is None or provider.type == "whatsapp_cloud":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("enabled") is True:
        # Enabling a non-WhatsApp channel (e.g. SMS) switches off everything
        # else, including every WhatsApp account — only one channel type is
        # active at a time, though multiple WhatsApp *accounts* within the
        # WhatsApp channel may be enabled together (see whatsapp-accounts).
        db.execute(
            CommunicationProvider.__table__.update()
            .where(CommunicationProvider.id != provider_id)
            .values(enabled=False)
        )
    for field, value in updates.items():
        setattr(provider, field, value)
    db.commit()
    return _to_provider_out(db, provider)


@router.post("/test-provider", dependencies=[Depends(require_role("Admin"))])
def test_provider_endpoint(payload: TestProviderRequest, db: Session = Depends(get_db)):
    provider = db.get(CommunicationProvider, payload.provider_id)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    return test_provider(provider)


def _whatsapp_account_row(db: Session, account_id: int) -> CommunicationProvider:
    provider = db.execute(
        select(CommunicationProvider).where(
            CommunicationProvider.id == account_id, CommunicationProvider.type == "whatsapp_cloud",
        )
    ).scalar_one_or_none()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "WhatsApp account not found")
    return provider


def _to_whatsapp_account_out(db: Session, provider: CommunicationProvider) -> WhatsAppAccountOut:
    return WhatsAppAccountOut(
        id=provider.id, name=provider.name, business_account_id=provider.business_account_id,
        phone_number_id=provider.phone_number_id, graph_version=provider.graph_version,
        use_templates=provider.use_templates, enabled=provider.enabled, is_default=provider.is_default,
        has_access_token=bool(provider.access_token_encrypted),
        has_webhook_verify_token=bool(provider.webhook_verify_token_encrypted),
        has_webhook_secret=bool(provider.webhook_secret_encrypted),
        business_name=provider.business_name, phone_number_display=provider.phone_number_display,
        api_version=provider.api_version, last_tested_at=provider.last_tested_at,
        last_test_status=provider.last_test_status, last_error=provider.last_error,
        messages_sent_today=_messages_sent_today(db, "whatsapp_cloud"),
        created_at=provider.created_at, updated_at=provider.updated_at,
    )


@router.get(
    "/whatsapp-accounts", response_model=list[WhatsAppAccountOut], dependencies=[Depends(require_role("Admin"))],
)
def list_whatsapp_accounts(db: Session = Depends(get_db)):
    accounts = db.execute(
        select(CommunicationProvider)
        .where(CommunicationProvider.type == "whatsapp_cloud")
        .order_by(CommunicationProvider.id)
    ).scalars().all()
    return [_to_whatsapp_account_out(db, a) for a in accounts]


@router.post(
    "/whatsapp-accounts", response_model=WhatsAppAccountOut, dependencies=[Depends(require_role("Admin"))],
)
def create_whatsapp_account(payload: WhatsAppAccountCreate, db: Session = Depends(get_db)):
    provider = CommunicationProvider(
        name=payload.name, type="whatsapp_cloud", enabled=payload.enabled,
        business_account_id=payload.business_account_id, phone_number_id=payload.phone_number_id,
        access_token_encrypted=encrypt(payload.access_token), graph_version=payload.graph_version,
        use_templates=payload.use_templates,
        webhook_verify_token_encrypted=encrypt(payload.webhook_verify_token),
        webhook_secret_encrypted=encrypt(payload.webhook_secret),
    )
    db.add(provider)
    db.commit()
    return _to_whatsapp_account_out(db, provider)


@router.put(
    "/whatsapp-accounts/{account_id}", response_model=WhatsAppAccountOut,
    dependencies=[Depends(require_role("Admin"))],
)
def update_whatsapp_account(account_id: int, payload: WhatsAppAccountUpdate, db: Session = Depends(get_db)):
    provider = _whatsapp_account_row(db, account_id)
    updates = payload.model_dump(exclude_unset=True)

    access_token = updates.pop("access_token", None)
    if access_token:  # blank/omitted keeps the existing encrypted token
        provider.access_token_encrypted = encrypt(access_token)
    webhook_verify_token = updates.pop("webhook_verify_token", None)
    if webhook_verify_token is not None:
        provider.webhook_verify_token_encrypted = encrypt(webhook_verify_token) if webhook_verify_token else None
    webhook_secret = updates.pop("webhook_secret", None)
    if webhook_secret is not None:
        provider.webhook_secret_encrypted = encrypt(webhook_secret) if webhook_secret else None

    for field, value in updates.items():
        setattr(provider, field, value)
    db.commit()
    return _to_whatsapp_account_out(db, provider)


@router.delete(
    "/whatsapp-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Admin"))],
)
def delete_whatsapp_account(account_id: int, db: Session = Depends(get_db)):
    provider = _whatsapp_account_row(db, account_id)
    db.delete(provider)
    db.commit()


@router.post(
    "/whatsapp-accounts/{account_id}/set-default", response_model=WhatsAppAccountOut,
    dependencies=[Depends(require_role("Admin"))],
)
def set_default_whatsapp_account(account_id: int, db: Session = Depends(get_db)):
    provider = _whatsapp_account_row(db, account_id)
    db.execute(
        CommunicationProvider.__table__.update()
        .where(CommunicationProvider.type == "whatsapp_cloud", CommunicationProvider.id != account_id)
        .values(is_default=False)
    )
    provider.is_default = True
    provider.enabled = True
    db.commit()
    return _to_whatsapp_account_out(db, provider)


@router.post(
    "/whatsapp-accounts/{account_id}/test", response_model=WhatsAppTestConnectionResult,
    dependencies=[Depends(require_role("Admin"))],
)
async def test_whatsapp_account(account_id: int, db: Session = Depends(get_db)):
    """Verifies the saved+decrypted credentials against the Graph API and
    persists the (non-secret) result onto this account's row. Never reads or
    returns the access token."""
    provider = _whatsapp_account_row(db, account_id)
    result = await WhatsAppCloudProvider.from_provider(provider).test_connection()

    provider.last_tested_at = datetime.now()
    provider.last_test_status = result["status"]
    provider.last_error = result.get("error")
    if result["status"] == "connected":
        provider.business_name = result.get("business_name")
        provider.phone_number_display = result.get("phone_number")
        provider.api_version = result.get("api_version")
    db.commit()

    if result["status"] != "connected":
        logger.warning("WhatsApp test_connection failed for account %s: %s", account_id, result.get("error"))
    return WhatsAppTestConnectionResult(**result)


@router.post(
    "/whatsapp-accounts/test-draft", response_model=WhatsAppTestConnectionResult,
    dependencies=[Depends(require_role("Admin"))],
)
async def test_whatsapp_account_draft(payload: WhatsAppAccountTestDraftRequest):
    """Tests unsaved credentials straight from the create/edit form — nothing
    is persisted, nothing is logged with the token."""
    provider = WhatsAppCloudProvider(
        access_token=payload.access_token, phone_number_id=payload.phone_number_id,
        business_account_id=payload.business_account_id or "", graph_version=payload.graph_version,
    )
    result = await provider.test_connection()
    if result["status"] != "connected":
        logger.warning("WhatsApp draft test_connection failed: %s", result.get("error"))
    return WhatsAppTestConnectionResult(**result)


@router.post(
    "/whatsapp-accounts/{account_id}/send-test-message", response_model=WhatsAppTestMessageResult,
    dependencies=[Depends(require_role("Admin"))],
)
async def send_whatsapp_account_test_message(
    account_id: int, payload: WhatsAppTestMessageRequest, db: Session = Depends(get_db),
):
    """Sends one approved-template message (default `hello_world`, which
    every WhatsApp Business app has pre-approved) directly via this account —
    bypasses the queue since this is a synchronous diagnostic action, not a
    business notification. Logged like any other send for traceability."""
    provider_row = _whatsapp_account_row(db, account_id)
    provider = WhatsAppCloudProvider.from_provider(provider_row)
    result = await provider.send_template(payload.recipient, payload.template_name, payload.language_code)

    db.add(NotificationLog(
        student_id=None, provider="whatsapp_cloud", recipient=payload.recipient,
        notification_type="test", message=f"[template] {payload.template_name}",
        status=result["status"], response=str(result.get("provider_response")) if result.get("provider_response") else None,
        error=result.get("error"), template=payload.template_name, meta_message_id=result.get("message_id"),
        http_status=result.get("http_status"), sent_at=datetime.now() if result["status"] == "sent" else None,
    ))
    db.commit()

    if result["status"] != "sent":
        logger.warning("WhatsApp test message failed for account %s: %s", account_id, result.get("error"))
    return WhatsAppTestMessageResult(**result)


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.execute(select(NotificationTemplate).order_by(NotificationTemplate.id)).scalars().all()


@router.put("/templates/{template_id}", response_model=TemplateOut, dependencies=[Depends(require_role("Admin"))])
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    template = db.get(NotificationTemplate, template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    db.commit()
    return template


def _assert_can_queue(current_user: CurrentUser, payload: QueueCreate, db: Session) -> None:
    if current_user.role_name == "Admin":
        return
    if current_user.role_name == "Accountant":
        if payload.notification_type not in ("custom", "fee_reminder"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Accountant can only send Custom Message or Fee Reminder.")
        return
    if current_user.role_name == "Teacher":
        if payload.notification_type != "attendance_absent":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Teacher can only trigger Attendance Absent notifications.")
        if payload.student_id is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Teacher must specify a student in their own class.")
        student = db.get(Student, payload.student_id)
        if student is None or student.class_name != current_user.assigned_class_name:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized for this student's class.")
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to send notifications.")


@router.post("/queue", response_model=QueueOut)
def create_queue_entry(
    payload: QueueCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _assert_can_queue(current_user, payload, db)
    return queue_notification(
        db,
        student_id=payload.student_id,
        recipient_name=payload.recipient_name,
        provider_type=payload.provider_type,
        notification_type=payload.notification_type,
        recipient=payload.recipient,
        message=payload.message,
        created_by=current_user.user_id,
    )


@router.post("/queue/bulk", response_model=list[QueueOut])
def create_queue_entries_bulk(
    payload: list[QueueCreate],
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Queues many notifications in one call — used by the Communication
    page's bulk actions (all absent today, selected pending-fee students,
    or a custom message to a selected group). Each row goes through the
    same role check as a single /queue call, so a mixed-permission batch
    fails loudly instead of silently sending what it can."""
    for entry in payload:
        _assert_can_queue(current_user, entry, db)
    return [
        queue_notification(
            db,
            student_id=entry.student_id,
            recipient_name=entry.recipient_name,
            provider_type=entry.provider_type,
            notification_type=entry.notification_type,
            recipient=entry.recipient,
            message=entry.message,
            created_by=current_user.user_id,
        )
        for entry in payload
    ]


@router.get("/queue", response_model=list[QueueOut], dependencies=[Depends(require_role("Admin", "Accountant"))])
def list_queue(status_filter: str | None = None, db: Session = Depends(get_db)):
    query = select(NotificationQueue).order_by(NotificationQueue.created_at.desc())
    if status_filter:
        query = query.where(NotificationQueue.status == status_filter)
    return db.execute(query).scalars().all()


@router.get("/history", response_model=list[HistoryOut], dependencies=[Depends(require_role("Admin", "Accountant"))])
def get_history(
    student_id: int | None = None,
    phone: str | None = None,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(NotificationLog).order_by(NotificationLog.created_at.desc())
    if student_id:
        query = query.where(NotificationLog.student_id == student_id)
    if phone:
        query = query.where(NotificationLog.recipient.ilike(f"%{phone}%"))
    if status_filter:
        query = query.where(NotificationLog.status == status_filter)
    if date_from:
        query = query.where(NotificationLog.created_at >= date_from)
    if date_to:
        query = query.where(NotificationLog.created_at <= date_to)
    return db.execute(query).scalars().all()


@router.get("/analytics", response_model=AnalyticsOut, dependencies=[Depends(require_role("Admin"))])
def get_analytics(db: Session = Depends(get_db)):
    """Feeds the Communication Overview card on the Admin dashboard: current
    queue health plus a 7-day sent/failed trend."""
    today = date.today()
    pending = db.execute(
        select(func.count()).select_from(NotificationQueue).where(NotificationQueue.status == "pending")
    ).scalar_one()
    processing = db.execute(
        select(func.count()).select_from(NotificationQueue).where(NotificationQueue.status == "processing")
    ).scalar_one()

    by_day: list[AnalyticsDayCount] = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        sent = db.execute(
            select(func.count()).select_from(NotificationLog).where(
                NotificationLog.status == "sent", NotificationLog.created_at >= day_start, NotificationLog.created_at < day_end,
            )
        ).scalar_one()
        failed = db.execute(
            select(func.count()).select_from(NotificationLog).where(
                NotificationLog.status == "failed", NotificationLog.created_at >= day_start, NotificationLog.created_at < day_end,
            )
        ).scalar_one()
        by_day.append(AnalyticsDayCount(day=day.isoformat(), sent=sent, failed=failed))

    sent_today = by_day[-1].sent
    failed_today = by_day[-1].failed

    return AnalyticsOut(pending=pending, processing=processing, sent_today=sent_today, failed_today=failed_today, by_day=by_day)
