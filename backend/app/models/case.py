import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.case_image import CaseImage


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus), default=CaseStatus.OPEN, index=True
    )
    
    # Clinical Patient Demographics
    patient_id_code: Mapped[str | None] = mapped_column(String(50), default=None)
    patient_name: Mapped[str | None] = mapped_column(String(120), default=None)
    age: Mapped[int | None] = mapped_column(Integer, default=None)
    gender: Mapped[str | None] = mapped_column(String(20), default=None)

    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, default=None
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    images: Mapped[list["CaseImage"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
