from sqlalchemy import Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class School(Base):
    __tablename__ = "school"

    school_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    # The logo lives in the database, not on disk: Render's filesystem is
    # ephemeral (wiped on every restart/deploy/idle spin-down), so a
    # disk-stored logo silently disappeared in production. Neon is the only
    # durable storage in this stack. logo_path remains only as a legacy
    # fallback for pre-existing local installs; bootstrap imports it into
    # logo_data on startup when possible.
    logo_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    logo_mime: Mapped[str | None] = mapped_column(String(50), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String, nullable=True)

    @property
    def has_logo(self) -> bool:
        return self.logo_data is not None or bool(self.logo_path)
    bank_name: Mapped[str] = mapped_column(String(255), default="")
    account_title: Mapped[str] = mapped_column(String(255), default="")
    account_number: Mapped[str] = mapped_column(String(100), default="")
    iban: Mapped[str] = mapped_column(String(100), default="")
    fee_due_day: Mapped[int] = mapped_column(Integer, default=10)
    challan_note: Mapped[str | None] = mapped_column(String, nullable=True)
