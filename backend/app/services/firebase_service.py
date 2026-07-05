"""Firebase Cloud Messaging sender.

Credentials come only from the environment or a git-ignored local file — never
hardcoded. Resolution order:
  1. FIREBASE_CREDENTIALS_JSON  — the service-account JSON inline (preferred on
     Render, where a file path isn't durable)
  2. FIREBASE_CREDENTIALS_FILE  — an explicit path to the service-account JSON
  3. backend/firebase/service-account.json — the conventional local file

Initialization is lazy and best-effort: if firebase-admin isn't installed or no
credentials are configured, the app keeps working and pushes are skipped (the
caller still persists the in-app notification and audit log). This keeps
local/CI and not-yet-configured deployments fully functional.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from app.config import settings
from app.logging_config import logger

# backend/firebase/service-account.json (app/services/ -> app -> backend)
_DEFAULT_CRED_FILE = Path(__file__).resolve().parents[2] / "firebase" / "service-account.json"

_lock = threading.Lock()
_app = None
_init_attempted = False
_available = False


def _load_credentials():
    """Returns a firebase_admin credentials.Certificate, or None if no source
    is configured / usable."""
    from firebase_admin import credentials

    if settings.firebase_credentials_json:
        return credentials.Certificate(json.loads(settings.firebase_credentials_json))
    if settings.firebase_credentials_file and Path(settings.firebase_credentials_file).is_file():
        return credentials.Certificate(settings.firebase_credentials_file)
    if _DEFAULT_CRED_FILE.is_file():
        return credentials.Certificate(str(_DEFAULT_CRED_FILE))
    return None


def _init() -> None:
    global _app, _init_attempted, _available
    if _init_attempted:
        return
    _init_attempted = True

    try:
        import firebase_admin  # noqa: F401
    except ImportError:
        logger.warning("firebase-admin not installed; push notifications disabled.")
        return

    try:
        cred = _load_credentials()
        if cred is None:
            logger.info("Firebase not configured (no FIREBASE_CREDENTIALS_*). Push disabled.")
            return
        _app = firebase_admin.initialize_app(cred, name="parent-fcm")
        _available = True
        logger.info("Firebase Cloud Messaging initialized.")
    except Exception:  # noqa: BLE001 — never let bad config crash the app
        logger.exception("Failed to initialize Firebase; push notifications disabled.")


def is_available() -> bool:
    with _lock:
        _init()
        return _available


def send_to_tokens(
    tokens: list[str],
    *,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    channel_id: str | None = None,
) -> tuple[int, int, list[str]]:
    """Send a data+notification message to many device tokens.

    ``channel_id`` pins the Android notification channel so the OS shows it with
    the right importance/sound — e.g. the high-importance "attendance_alerts"
    channel makes an absent alert a proper heads-up notification with sound,
    rather than a silent one on the default channel.

    Returns ``(delivered, failed, invalid_tokens)``. ``invalid_tokens`` are
    tokens FCM reported as unregistered/invalid so the caller can prune them.
    When Firebase is unavailable, everything counts as failed and no tokens are
    reported invalid (they may still be good once Firebase is configured).
    """
    tokens = [t for t in tokens if t]
    if not tokens:
        return (0, 0, [])

    with _lock:
        _init()
        if not _available:
            return (0, len(tokens), [])

        from firebase_admin import messaging

        delivered = 0
        failed = 0
        invalid: list[str] = []
        for start in range(0, len(tokens), 500):  # FCM caps multicast at 500
            chunk = tokens[start:start + 500]
            message = messaging.MulticastMessage(
                tokens=chunk,
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id=channel_id or "school_announcements",
                        sound="default",
                        default_vibrate_timings=True,
                    ),
                ),
            )
            try:
                response = messaging.send_each_for_multicast(message, app=_app)
            except Exception:  # noqa: BLE001
                logger.exception("FCM multicast send failed for a chunk")
                failed += len(chunk)
                continue
            for token, result in zip(chunk, response.responses):
                if result.success:
                    delivered += 1
                else:
                    failed += 1
                    exc = result.exception
                    name = type(exc).__name__ if exc else ""
                    if name in ("UnregisteredError", "SenderIdMismatchError", "InvalidArgumentError"):
                        invalid.append(token)
        return (delivered, failed, invalid)
