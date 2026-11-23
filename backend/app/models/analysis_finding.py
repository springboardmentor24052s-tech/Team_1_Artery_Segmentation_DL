from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.case_image import CaseImage


class AnalysisFinding(Base):
    """
    Stores quantitative QCA morphometric measurements, Grad-CAM XAI paths,
    and 5-category stenosis severity classifications.
    """
    __tablename__ = "analysis_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("case_images.id", ondelete="CASCADE"), index=True
    )
    lesion_id: Mapped[int] = mapped_column(Integer, default=1)
    
    # Bounding Box & Centroid Coordinates (JSON string)
    bbox_json: Mapped[str] = mapped_column(String(100), default="[]")
    centroid_json: Mapped[str] = mapped_column(String(50), default="[]")
    probability_stenosis: Mapped[float] = mapped_column(Float, default=0.0)

    # QCA Quantitative Calipers
    mld_mm: Mapped[float] = mapped_column(Float, default=0.0)  # Minimum Lumen Diameter
    rvd_mm: Mapped[float] = mapped_column(Float, default=0.0)  # Reference Vessel Diameter
    pct_stenosis: Mapped[float] = mapped_column(Float, default=0.0)  # % Diameter Stenosis
    lesion_length_mm: Mapped[float] = mapped_column(Float, default=0.0)

    # Anatomical Branch Mapping (AHA 15-Segment Tree)
    coronary_branch: Mapped[str] = mapped_column(String(120), default="LAD")
    segment_code: Mapped[str] = mapped_column(String(50), default="LAD-Mid")

    # Standardized 5 Severity Categories:
    # 1. Normal | 2. Mild | 3. Moderate | 4. Severe | 5. Critical
    severity_category: Mapped[str] = mapped_column(String(50), index=True, default="Normal")
    clinical_label: Mapped[str] = mapped_column(String(200), default="")
    hemodynamic_significance: Mapped[str] = mapped_column(String(200), default="")
    clinical_recommendation: Mapped[str] = mapped_column(Text, default="")

    # Medical Image Storage Keys (Local Multi-Tier Storage)
    xai_plot_key: Mapped[str | None] = mapped_column(String(500), default=None)
    mask_key: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Inference Latency
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Reverse Relationship
    image: Mapped["CaseImage"] = relationship(back_populates="findings")

