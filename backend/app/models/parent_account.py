from datetime import datetime

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParentAccount(Base):
    """A parent login, living inside a single school's (tenant) database and
    keyed by mobile number. The link to students is not a foreign key: one
    mobile number may belong to several students (matched at query time against
    student_contact / student.phone). Default password is the mobile number
    itself (bcrypt-hashed). The master parent_directory maps this mobile to
    this school so login can route here."""

    __tablename__ = "parent_account"

    parent_id: Mapped[int] = mapped_column(primary_key=True)
    mobile_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
