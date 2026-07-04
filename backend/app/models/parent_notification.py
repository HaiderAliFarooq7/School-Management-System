from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParentNotification(Base):
    """Per-parent inbox row — the notification history the parent app shows
    (and its offline source of truth). One admin/automatic send produces one
    notification_log row plus one ParentNotification per recipient parent.
    ``notif_type`` is 'absent' | 'fee_reminder' | 'announcement'; ``student_id``
    scopes the deep-link when the notification is about a specific child."""

    __tablename__ = "parent_notification"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("parent_account.parent_id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("student.student_id", ondelete="SET NULL"), nullable=True
    )
    notif_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
