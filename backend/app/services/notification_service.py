import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.communication_provider import CommunicationProvider
from app.models.notification_log import NotificationLog
from app.models.notification_queue import NotificationQueue
from app.models.notification_template import NotificationTemplate
from app.services.providers import get_provider_instance

MAX_RETRIES = 3

# Maps a CommunicationProvider.type (the concrete placeholder implementation)
# to the channel it serves. NotificationQueue.provider_type/notification
# requests are always expressed in terms of the channel ("sms"/"whatsapp"),
# never the concrete implementation — that's the whole point of the
# abstraction: swapping android_gateway for a different sms implementation
# later needs no caller-side change.
CHANNEL_BY_PROVIDER_TYPE = {
    "android_gateway": "sms",
    "whatsapp_cloud": "whatsapp",
}

VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_template(message: str, variables: dict) -> str:
    """Replaces `{{var}}` placeholders with values from `variables`. Unknown
    placeholders are left blank rather than raising, so a missing optional
    variable (e.g. {{remaining_fee}} on a fully-paid reminder) never blocks
    sending."""
    return VAR_PATTERN.sub(lambda m: str(variables.get(m.group(1), "")), message)


def render_named_template(db: Session, template_name: str, variables: dict) -> str:
    template = db.execute(
        select(NotificationTemplate).where(NotificationTemplate.name == template_name)
    ).scalar_one_or_none()
    if template is None or not template.enabled:
        raise ValueError(f"Template '{template_name}' not found or disabled.")
    return render_template(template.message, variables)


def get_active_provider(db: Session, channel: str) -> CommunicationProvider | None:
    """The CommunicationProvider that serves `channel` ("sms"/"whatsapp") and
    should be used to send right now. Multiple `whatsapp_cloud` rows may be
    enabled at once (multi-account) — among those, the one flagged
    `is_default` wins; if none is flagged, fall back to the first enabled row
    so the system keeps working even if an admin forgot to set a default.
    Other provider types (e.g. android_gateway) only ever have one enabled
    row, so this degrades to the old single-provider lookup for them."""
    providers = db.execute(select(CommunicationProvider).where(CommunicationProvider.enabled.is_(True))).scalars().all()
    candidates = [p for p in providers if CHANNEL_BY_PROVIDER_TYPE.get(p.type) == channel]
    if not candidates:
        return None
    for provider in candidates:
        if provider.is_default:
            return provider
    return candidates[0]


def get_enabled_channel(db: Session) -> str | None:
    """Which channel ("sms"/"whatsapp") the currently-enabled provider
    serves, or None if no provider is enabled. Callers that don't have a
    user-chosen channel (e.g. automatic attendance-absent notifications)
    should queue against this rather than a hardcoded channel, so the
    notification actually goes out through whichever provider the school
    has switched on — switching providers in the Providers tab then needs
    no code change anywhere else."""
    provider = db.execute(select(CommunicationProvider).where(CommunicationProvider.enabled.is_(True))).scalars().first()
    return CHANNEL_BY_PROVIDER_TYPE.get(provider.type) if provider else None


def queue_notification(
    db: Session,
    *,
    provider_type: str,
    notification_type: str,
    recipient: str,
    message: str,
    student_id: int | None = None,
    recipient_name: str | None = None,
    created_by: int | None = None,
) -> NotificationQueue:
    """Inserts a pending notification and returns immediately — the actual
    send always happens later in process_queue(), never inline here. Callers
    (attendance, fee reminders, custom message) never talk to a provider
    directly."""
    entry = NotificationQueue(
        student_id=student_id,
        recipient_name=recipient_name,
        provider_type=provider_type,
        recipient=recipient,
        notification_type=notification_type,
        message=message,
        status="pending",
        created_by=created_by,
    )
    db.add(entry)
    db.commit()
    return entry


def _whatsapp_template_override(db: Session, notification_type: str) -> str | None:
    """The matching NotificationTemplate's `whatsapp_template_name`, if an
    admin has set one — lets a newly Meta-approved template be wired in from
    the Templates tab, with no code change to the provider's built-in map."""
    template = db.execute(
        select(NotificationTemplate.whatsapp_template_name).where(NotificationTemplate.type == notification_type)
    ).scalar_one_or_none()
    return template


def _send_via_provider(
    provider: CommunicationProvider, channel: str, to: str, message: str,
    notification_type: str | None = None, template_override: str | None = None,
) -> dict:
    """Generic single-shot send through whichever provider class matches
    `provider.type` — used for both the ad-hoc Test Provider action and the
    queue processor below. `notification_type`/`template_override` only
    matter for WhatsApp (template-vs-text selection)."""
    instance = get_provider_instance(provider)
    if instance is None:
        return {"status": "failed", "error": f"Unknown provider implementation '{provider.type}'."}
    if channel == "whatsapp":
        return instance.send_whatsapp(
            to, message, provider.configuration_json or {},
            notification_type=notification_type, template_override=template_override,
        )
    return instance.send_sms(to, message, provider.configuration_json or {})


def _process_one(db: Session, entry: NotificationQueue) -> None:
    entry.status = "processing"
    db.commit()

    provider = get_active_provider(db, entry.provider_type)
    if provider is None:
        result = {"status": "failed", "error": f"No active provider enabled for channel '{entry.provider_type}'."}
    else:
        template_override = (
            _whatsapp_template_override(db, entry.notification_type) if entry.provider_type == "whatsapp" else None
        )
        result = _send_via_provider(
            provider, entry.provider_type, entry.recipient, entry.message,
            notification_type=entry.notification_type, template_override=template_override,
        )

    now = datetime.now()
    log = NotificationLog(
        student_id=entry.student_id,
        provider=provider.type if provider else None,
        recipient=entry.recipient,
        notification_type=entry.notification_type,
        message=entry.message,
        status=result["status"],
        response=str(result.get("provider_response")) if result.get("provider_response") else None,
        error=result.get("error"),
        sent_at=now if result["status"] == "sent" else None,
        template=result.get("template_name"),
        meta_message_id=result.get("message_id"),
        http_status=result.get("http_status"),
    )
    db.add(log)

    if result["status"] == "sent":
        entry.status = "sent"
        entry.sent_at = now
        entry.provider_response = str(result.get("provider_response")) if result.get("provider_response") else None
        entry.error_message = None
    else:
        entry.retry_count += 1
        entry.error_message = result.get("error")
        if entry.retry_count >= MAX_RETRIES:
            entry.status = "failed"
        else:
            entry.status = "pending"
            entry.scheduled_at = now + timedelta(minutes=2 ** entry.retry_count)
    db.commit()


def process_queue(db: Session, limit: int = 50) -> dict:
    """Sends every pending notification whose scheduled_at has arrived (or is
    unset). Meant to be called by a periodic background loop — see
    app.main's startup task — never by a request handler directly."""
    now = datetime.now()
    entries = db.execute(
        select(NotificationQueue)
        .where(
            NotificationQueue.status == "pending",
            (NotificationQueue.scheduled_at.is_(None)) | (NotificationQueue.scheduled_at <= now),
        )
        .order_by(NotificationQueue.created_at)
        .limit(limit)
    ).scalars().all()

    sent = failed = retried = 0
    for entry in entries:
        was_retry = entry.retry_count > 0
        _process_one(db, entry)
        if entry.status == "sent":
            sent += 1
        elif entry.status == "failed":
            failed += 1
        elif was_retry or entry.retry_count > 0:
            retried += 1
    return {"processed": len(entries), "sent": sent, "failed": failed, "retried": retried}


def test_provider(provider: CommunicationProvider) -> dict:
    """Calls the placeholder provider directly with a dummy message — used by
    the Providers tab's "Test Provider" action. Never touches the queue or
    log; purely a connectivity/config sanity check against the interface."""
    channel = CHANNEL_BY_PROVIDER_TYPE.get(provider.type)
    if channel is None:
        return {"status": "failed", "error": f"Unknown provider implementation '{provider.type}'."}
    return _send_via_provider(provider, channel, "+10000000000", "Test message from Communication Settings.")
