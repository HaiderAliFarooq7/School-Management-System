"""Placeholder SMS provider — an Android-phone SMS gateway app.

Still a mock (returns success without calling a real gateway). Kept as the
proof that the provider architecture is swappable: this can be fleshed out into
a real gateway later with no change to the queue or any business module — the
same way WhatsAppCloudProvider was made real.

Expected `config` keys (from the DB row's configuration_json): phone_id,
api_url, websocket_url, auth_token.
"""
from app.services.providers.base import NotificationProvider, mock_response


class AndroidGatewayProvider(NotificationProvider):
    def send_sms(self, to: str, message: str, config: dict) -> dict:
        if not config.get("phone_id") or not config.get("auth_token"):
            return {"status": "failed", "error": "AndroidGateway config missing phone_id/auth_token."}
        return {
            "status": "sent",
            "provider_response": mock_response(provider="android_gateway", phone_id=config.get("phone_id"), to=to),
        }
