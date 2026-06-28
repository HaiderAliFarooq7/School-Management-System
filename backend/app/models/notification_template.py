from datetime import datetime

from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationTemplate(Base):
    """A reusable message template. `message` uses `{{var}}` placeholders
    (e.g. `{{student_name}}`); `variables` lists the placeholder names this
    template expects, for the frontend's preview/variable-picker UI."""

    __tablename__ = "notification_template"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="general")
    message: Mapped[str] = mapped_column(String, nullable=False)
    variables: Mapped[list] = mapped_column(JSONB, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Name of the Meta-approved WhatsApp template to use for this message
    # type (e.g. "pending_fee"), when whatsapp_use_templates is on. Overrides
    # WhatsAppCloudProvider's built-in TEMPLATE_BY_NOTIFICATION_TYPE mapping
    # without a code change. Null = use the built-in default for this type.
    whatsapp_template_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
