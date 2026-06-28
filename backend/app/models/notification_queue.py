from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationQueue(Base):
    """A single pending/in-flight notification. `provider_type` is the
    channel needed (sms/whatsapp) — the processor looks up the single
    enabled CommunicationProvider of that type at send time, so callers
    never talk to a concrete provider themselves. Attendance/Fee/Custom
    Message all insert rows here and return immediately; a background
    worker (see notification_service.process_queue) does the actual send."""

    __tablename__ = "notification_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("student.student_id", ondelete="SET NULL"), nullable=True
    )
    recipient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    provider_type: Mapped[str] = mapped_column(String(30), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_response: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.user_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
