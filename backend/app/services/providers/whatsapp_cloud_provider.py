"""Production Meta WhatsApp Cloud API provider.

Talks to the Graph API (`https://graph.facebook.com/{version}`) over
`httpx.AsyncClient` with bearer auth, timeouts, transient-error retries, and
structured error handling. Credentials are passed in explicitly at
construction time — either decrypted from a saved `CommunicationProvider` row
(`from_provider`, used by the queue/test-saved-account paths) or straight from
an unsaved form (`__init__` directly, used by the "test before saving"
endpoint). The access token is never logged or returned through the API.

The async methods (`connect`, `test_connection`, `send_template`,
`send_text_message`, ...) are awaited directly by the dedicated
test/diagnostic endpoints. The notification queue is synchronous, so it calls
the inherited `send_whatsapp(...)` which bridges into the async layer via
`_run_sync` (safe whether or not an event loop is already running).
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import typing

import httpx

from app.logging_config import logger
from app.services.crypto import decrypt
from app.services.providers.base import NotificationProvider

if typing.TYPE_CHECKING:
    from app.models.communication_provider import CommunicationProvider

# Maps our internal notification_type -> the approved WhatsApp template name.
# These names must match templates approved in the Meta dashboard. Each is
# expected to have a single body parameter {{1}} which we fill with the fully
# rendered message text (variable substitution already done upstream).
TEMPLATE_BY_NOTIFICATION_TYPE = {
    "attendance_absent": "attendance_absent",
    "fee_reminder": "pending_fee",
    "custom": "custom_message",
    "custom_message": "custom_message",
}

# Friendly messages for the Meta error codes a school will actually hit.
_META_ERROR_HINTS = {
    190: "Access token is invalid or has expired. Generate a new token.",
    102: "Session/access token is invalid. Generate a new token.",
    131030: "Recipient phone number is not in the allowed list (add it in the Meta dashboard, or the number hasn't opted in).",
    131047: "Outside the 24-hour window — an approved template message is required to reach this number.",
    131026: "Message undeliverable — the recipient may not have WhatsApp or hasn't accepted the latest terms.",
    132001: "Template does not exist or is not approved for this language/category.",
    132000: "Template parameter count mismatch.",
    100: "Invalid request parameter (check the phone number format or template name).",
    80007: "Rate limit reached. Try again shortly.",
    130429: "Rate limit reached. Try again shortly.",
    133010: "Phone number not registered on WhatsApp Cloud API.",
    10: "Missing permissions for this WhatsApp Business asset — check the access token's granted permissions.",
    200: "Missing permissions for this action — the access token may lack the whatsapp_business_messaging permission.",
    803: "Invalid Phone Number ID — check the account's configured Phone Number ID.",
}

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def _run_sync(coro):
    """Run an async coroutine from sync code, whether or not an event loop is
    already running on this thread (the queue worker runs process_queue via
    asyncio.to_thread, so normally there is no running loop here)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(lambda: asyncio.run(coro)).result()


def _normalize_phone(raw: str) -> str:
    """Meta wants an international number with country code and no symbols.
    Strips spaces/dashes/`+`; converts a local PK 0-prefixed number
    (e.g. 03001234567) to 92-prefixed (923001234567)."""
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if digits.startswith("0") and len(digits) == 11:
        digits = "92" + digits[1:]
    return digits


def _meta_error_message(error: dict) -> str:
    """Surfaces the real Meta error (code + message + details) with a friendly hint."""
    code = error.get("code")
    parts = []
    if code in _META_ERROR_HINTS:
        parts.append(_META_ERROR_HINTS[code])
    msg = error.get("message")
    if msg:
        parts.append(msg)
    details = (error.get("error_data") or {}).get("details")
    if details:
        parts.append(str(details))
    if not parts:
        parts.append("Unknown error from WhatsApp Cloud API.")
    suffix = f" (code {code})" if code is not None else ""
    return " ".join(parts) + suffix


class WhatsAppConfigError(Exception):
    """Raised when required WhatsApp env credentials are missing."""


class WhatsAppCloudProvider(NotificationProvider):
    DEFAULT_TIMEOUT = 20.0
    MAX_RETRIES = 3

    def __init__(
        self, *, access_token: str, phone_number_id: str, business_account_id: str = "",
        graph_version: str = "v25.0", use_templates: bool = False,
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.business_account_id = business_account_id
        self.graph_version = graph_version or "v25.0"
        self.use_templates = use_templates
        self.base_url = f"https://graph.facebook.com/{self.graph_version}"

    @classmethod
    def from_provider(cls, provider: "CommunicationProvider") -> "WhatsAppCloudProvider":
        """Builds an instance from a saved `CommunicationProvider` row,
        decrypting its access token. Used by the queue processor and the
        "test saved account" endpoint."""
        return cls(
            access_token=decrypt(provider.access_token_encrypted) or "",
            phone_number_id=provider.phone_number_id or "",
            business_account_id=provider.business_account_id or "",
            graph_version=provider.graph_version or "v25.0",
            use_templates=provider.use_templates,
        )

    # ----------------------------------------------------------------- config
    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def connect(self) -> dict:
        """Validates that the required credentials are present (does not hit the
        network). Raises WhatsAppConfigError listing whatever is missing."""
        missing = [
            name for name, value in (
                ("Access Token", self.access_token),
                ("Phone Number ID", self.phone_number_id),
            ) if not value
        ]
        if missing:
            raise WhatsAppConfigError("Missing required WhatsApp account fields: " + ", ".join(missing))
        return {"configured": True, "graph_version": self.graph_version}

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    # --------------------------------------------------------------- requests
    async def test_connection(self) -> dict:
        """Verifies the credentials against the Graph API and returns the
        business name, display phone number, and API version. Never returns the
        token."""
        try:
            self.connect()
        except WhatsAppConfigError as exc:
            return {"status": "disconnected", "error": str(exc)}

        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                phone_resp = await client.get(
                    f"{self.base_url}/{self.phone_number_id}",
                    headers=self._headers(),
                    params={"fields": "verified_name,display_phone_number,quality_rating"},
                )
                phone_data = phone_resp.json() if phone_resp.content else {}
                if phone_resp.status_code != 200:
                    return {
                        "status": "disconnected",
                        "http_status": phone_resp.status_code,
                        "error": _meta_error_message(phone_data.get("error") or {}),
                    }

                business_name = phone_data.get("verified_name")
                if self.business_account_id:
                    waba_resp = await client.get(
                        f"{self.base_url}/{self.business_account_id}",
                        headers=self._headers(),
                        params={"fields": "name"},
                    )
                    if waba_resp.status_code == 200 and waba_resp.content:
                        business_name = waba_resp.json().get("name") or business_name

            return {
                "status": "connected",
                "business_name": business_name,
                "phone_number": phone_data.get("display_phone_number"),
                "quality_rating": phone_data.get("quality_rating"),
                "api_version": self.graph_version,
            }
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            logger.warning("WhatsApp test_connection network error: %s", exc)
            return {"status": "disconnected", "error": f"Could not reach WhatsApp Cloud API: {exc}"}

    async def _post_message(self, payload: dict) -> dict:
        """POSTs a message payload to /{phone_number_id}/messages with retries
        on transient errors. Returns the standardized provider result dict."""
        try:
            self.connect()
        except WhatsAppConfigError as exc:
            return {"status": "failed", "error": str(exc)}

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        last_error = "Unknown error"
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    resp = await client.post(url, headers=self._headers(), json=payload)
                    data = resp.json() if resp.content else {}
                    if resp.status_code == 200:
                        message_id = ((data.get("messages") or [{}])[0]).get("id")
                        return {
                            "status": "sent",
                            "message_id": message_id,
                            "http_status": resp.status_code,
                            "provider_response": data,
                        }
                    error = data.get("error") or {}
                    last_error = _meta_error_message(error)
                    if resp.status_code in _RETRYABLE_HTTP and attempt < self.MAX_RETRIES:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return {
                        "status": "failed",
                        "http_status": resp.status_code,
                        "error": last_error,
                        "provider_response": data,
                    }
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = f"Network error contacting WhatsApp Cloud API: {exc}"
                    logger.warning("WhatsApp send attempt %d failed: %s", attempt, exc)
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(2 ** attempt)
                        continue
        return {"status": "failed", "error": last_error}

    async def send_text_message(self, to: str, text: str) -> dict:
        """Free-form text message — only delivered inside the 24-hour window."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_phone(to),
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        return await self._post_message(payload)

    async def send_template(
        self, to: str, template_name: str, language_code: str = "en_US", body_params: list[str] | None = None
    ) -> dict:
        """Pre-approved template message — works outside the 24-hour window.
        `body_params` fill the template's body {{1}}, {{2}}, ... in order."""
        components = []
        if body_params:
            components = [{
                "type": "body",
                "parameters": [{"type": "text", "text": str(p)} for p in body_params],
            }]
        template: dict = {"name": template_name, "language": {"code": language_code}}
        if components:
            template["components"] = components
        payload = {
            "messaging_product": "whatsapp",
            "to": _normalize_phone(to),
            "type": "template",
            "template": template,
        }
        return await self._post_message(payload)

    # ------------------------------------- per-notification-type send helpers
    async def _send_typed(
        self, to: str, rendered_text: str, notification_type: str | None, template_override: str | None = None
    ) -> dict:
        """Sends as an approved template (when enabled and one is mapped),
        otherwise as free text. The rendered text — variables already
        substituted — is passed as the template's single body parameter.
        `template_override` (the matching NotificationTemplate's
        `whatsapp_template_name`, looked up by the caller) takes priority
        over the built-in TEMPLATE_BY_NOTIFICATION_TYPE mapping, so an admin
        can point at a newly-approved Meta template without a code change."""
        template_name = template_override or TEMPLATE_BY_NOTIFICATION_TYPE.get(notification_type or "")
        if self.use_templates and template_name:
            result = await self.send_template(to, template_name, body_params=[rendered_text])
            result["template_name"] = template_name
            return result
        return await self.send_text_message(to, rendered_text)

    async def send_custom_message(self, to: str, text: str, template_override: str | None = None) -> dict:
        return await self._send_typed(to, text, "custom", template_override)

    async def send_fee_reminder(self, to: str, text: str, template_override: str | None = None) -> dict:
        return await self._send_typed(to, text, "fee_reminder", template_override)

    async def send_attendance_absent(self, to: str, text: str, template_override: str | None = None) -> dict:
        return await self._send_typed(to, text, "attendance_absent", template_override)

    # ----------------------------------------------- queue-facing sync bridge
    def send_whatsapp(
        self, to: str, message: str, config: dict, notification_type: str | None = None,
        template_override: str | None = None,
    ) -> dict:
        """Synchronous entry point the notification queue calls. Bridges into
        the async Graph API layer. `config` (the DB row) is ignored — all
        credentials come from the environment."""
        return _run_sync(self._send_typed(to, message, notification_type, template_override))
