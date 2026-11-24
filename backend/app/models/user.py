import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Role(str, enum.Enum):
    # Canonical Platform Roles
    DEVELOPER = "Developer"
    RADIOLOGIST_CLINICIAN = "Radiologist / Clinician"
    MEDICAL_RESEARCHER = "Medical Researcher"
    DATA_SCIENTIST = "Data Scientist"
    ADMINISTRATOR = "Administrator"

    # Compatibility Aliases
    DEV = DEVELOPER
    LEAD_DEV = DEVELOPER
    ADMIN = ADMINISTRATOR
    RADIOLOGIST = RADIOLOGIST_CLINICIAN
    CLINICIAN = RADIOLOGIST_CLINICIAN
    DOCTOR = RADIOLOGIST_CLINICIAN
    PRINCIPAL_INVESTIGATOR = MEDICAL_RESEARCHER
    AI_RESEARCH_FELLOW = DATA_SCIENTIST
    LAB_TECHNICIAN = DATA_SCIENTIST
    PATIENT = RADIOLOGIST_CLINICIAN


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(60), default=Role.DATA_SCIENTIST.value)
    department: Mapped[str] = mapped_column(String(100), default="StenoVision AI Core")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
