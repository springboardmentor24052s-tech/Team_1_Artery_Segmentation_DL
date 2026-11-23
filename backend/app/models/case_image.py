from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.analysis_finding import AnalysisFinding


class CaseImage(Base):
    __tablename__ = "case_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))  # display filename
    file_key: Mapped[str] = mapped_column(String(500), unique=True)  # path in local storage
    storage_tier: Mapped[str] = mapped_column(String(50), default="raw")  # raw, masks, xai
    modality: Mapped[str] = mapped_column(String(50), default="XCA")  # XCA, DICOM
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)  # integrity check
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="images")
    findings: Mapped[list["AnalysisFinding"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )
