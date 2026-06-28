from datetime import datetime

from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommunicationProvider(Base):
    """A configured channel/provider (e.g. an SMS gateway or a WhatsApp Cloud
    API business account). `type` identifies which provider implementation to
    use (android_gateway/whatsapp_cloud). Multiple `whatsapp_cloud` rows may
    exist (multi-account) and multiple may be `enabled` simultaneously; at
    most one is `is_default` — that's the one the queue processor sends
    through. Enabling a non-whatsapp provider still disables every other row
    (single-channel exclusivity), enforced in the router.

    `configuration_json` holds provider-specific config for providers whose
    credentials live in the DB unencrypted (e.g. android_gateway, a
    placeholder). WhatsApp credentials are encrypted (see
    app.services.crypto) and stored in the dedicated `*_encrypted` columns
    below — never in `configuration_json`, never returned through the API.
    The `business_name`..`last_error` columns are read-only diagnostic state
    populated by Test Connection, purely for display (see
    app.services.providers.whatsapp_cloud_provider)."""

    __tablename__ = "communication_provider"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    configuration_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    # WhatsApp Cloud account configuration (encrypted fields hold ciphertext,
    # never plaintext). Unused for other provider types.
    business_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    graph_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    webhook_verify_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    webhook_secret_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    use_templates: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Diagnostic state from the last successful/failed Test Connection —
    # never a secret, safe to return through the API.
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number_display: Mapped[str | None] = mapped_column(String(50), nullable=True)
    api_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
