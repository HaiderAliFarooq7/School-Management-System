from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QRCode(Base):
    __tablename__ = "qr_code"

    qr_id: Mapped[int] = mapped_column(primary_key=True)
    voucher_id: Mapped[int] = mapped_column(
        ForeignKey("fee_voucher.voucher_id", ondelete="CASCADE"), nullable=False
    )
    qr_code_text: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())
