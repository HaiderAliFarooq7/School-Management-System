from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Grade(Base):
    __tablename__ = "grade"

    grade_id: Mapped[int] = mapped_column(primary_key=True)
    class_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    fee_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
