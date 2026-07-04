from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationLog(Base):
    """Admin-side audit record of one notification send (automatic or manual),
    per school database. ``audience`` is 'student' | 'class' | 'school';
    ``notif_type`` is 'absent' | 'fee_reminder' | 'announcement'. Delivery
    counts summarise the FCM fan-out. Distinct from parent_notification, which
    is the per-parent inbox copy."""

    __tablename__ = "notification_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    notif_type: Mapped[str] = mapped_column(String(30), nullable=False)
    audience: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("student.student_id", ondelete="SET NULL"), nullable=True
    )
    class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sent_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.user_id", ondelete="SET NULL"), nullable=True
    )
    recipients_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
