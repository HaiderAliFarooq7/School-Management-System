"""Stable provider interface for the Communication Module.

Every concrete provider implements this interface. The notification queue only
ever talks to a provider through these methods, so a provider (e.g. WhatsApp
Cloud) can be swapped for another (e.g. an Android SMS gateway) without any
change to Attendance, Fee Reminder, Student, or Communication code.

Return contract for the queue-facing methods:
    {"status": "sent"|"failed",
     "message_id": str | None,        # provider message id, when available
     "http_status": int | None,       # upstream HTTP status, when applicable
     "provider_response": dict | None,
     "error": str | None}
"""
import uuid
from abc import ABC


class NotificationProvider(ABC):
    """Base interface. A provider that cannot perform a given channel returns a
    failed dict rather than raising, so the queue processor never crashes on a
    channel mismatch."""

    def send_sms(self, to: str, message: str, config: dict) -> dict:
        return {"status": "failed", "error": f"{self.__class__.__name__} does not support SMS."}

    def send_whatsapp(
        self, to: str, message: str, config: dict, notification_type: str | None = None,
        template_override: str | None = None,
    ) -> dict:
        return {"status": "failed", "error": f"{self.__class__.__name__} does not support WhatsApp."}


def mock_response(**extra) -> dict:
    return {"mock": True, "message_id": str(uuid.uuid4()), **extra}
