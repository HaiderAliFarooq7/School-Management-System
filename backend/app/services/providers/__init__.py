"""The provider-independent sending layer for the Communication Module.

`PROVIDER_CLASSES` maps a `CommunicationProvider.type` to its concrete
implementation. NotificationService (the only caller) looks a provider row up
by type and talks to it purely through the `NotificationProvider` interface —
swapping `whatsapp_cloud` for a different WhatsApp/SMS implementation later
needs a new class added here, nothing else."""

import typing

from app.services.providers.android_gateway_provider import AndroidGatewayProvider
from app.services.providers.base import NotificationProvider, mock_response
from app.services.providers.whatsapp_cloud_provider import WhatsAppCloudProvider, WhatsAppConfigError

if typing.TYPE_CHECKING:
    from app.models.communication_provider import CommunicationProvider

PROVIDER_CLASSES: dict[str, type[NotificationProvider]] = {
    "android_gateway": AndroidGatewayProvider,
    "whatsapp_cloud": WhatsAppCloudProvider,
}


def get_provider_instance(provider: "CommunicationProvider") -> NotificationProvider | None:
    """`whatsapp_cloud` needs the row itself (to decrypt its credentials);
    every other provider type is stateless and takes no constructor args."""
    cls = PROVIDER_CLASSES.get(provider.type)
    if cls is None:
        return None
    if provider.type == "whatsapp_cloud":
        return WhatsAppCloudProvider.from_provider(provider)
    return cls()


__all__ = [
    "NotificationProvider",
    "AndroidGatewayProvider",
    "WhatsAppCloudProvider",
    "WhatsAppConfigError",
    "PROVIDER_CLASSES",
    "get_provider_instance",
    "mock_response",
]
