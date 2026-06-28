from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable: a diagnostic send (e.g. WhatsApp "Send Test Message") or a
    # custom message to a non-student recipient has no student to attach.
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("student.student_id", ondelete="SET NULL"), nullable=True
    )
    notification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Expanded fields for the provider-independent communication module.
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    response: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Populated when the provider is WhatsAppCloudProvider: which template
    # (if any) was used, Meta's own message id, and the upstream HTTP status
    # — lets an admin trace a failed send back to the exact Graph API call.
    template: Mapped[str | None] = mapped_column(String(150), nullable=True)
    meta_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
