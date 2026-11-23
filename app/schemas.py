from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ROLES


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _email(v: str) -> str:
    v = v.strip().lower()
    if "@" not in v or "." not in v.split("@")[-1] or " " in v:
        raise ValueError("Invalid email address")
    return v


class RegisterIn(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=200)
    password: str
    role: str = "radiologist"
    organization: str | None = None
    @field_validator("email")
    @classmethod
    def _em(cls, v):
        return _email(v)

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        if v not in ROLES or v == "admin":
            raise ValueError("Role must be radiologist, researcher or data_scientist")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    role: str
    organization: str | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None
    locked: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    organization: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        if v is not None and v not in ROLES:
            raise ValueError("Invalid role")
        return v


class PatientIn(BaseModel):
    patient_code: str = Field(min_length=1, max_length=50)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = None
    medical_history: str | None = None
    risk_factors: list[str] = []
    clinical_notes: str | None = None


class PatientOut(ORM):
    id: int
    patient_code: str
    age: int | None
    gender: str | None
    medical_history: str | None
    risk_factors: list[str]
    clinical_notes: str | None
    created_at: datetime


class CaseIn(BaseModel):
    patient_id: int
    modality: str = "X-ray Coronary Angiography"
    scan_date: str | None = None
    anatomical_region: str = "Coronary arteries"
    notes: str | None = None


class CaseOut(ORM):
    id: int
    case_code: str
    patient_id: int
    modality: str
    scan_date: str | None
    anatomical_region: str
    status: str
    notes: str | None
    created_at: datetime


class ImageOut(ORM):
    id: int
    case_id: int
    filename: str
    file_format: str
    width: int
    height: int
    pixel_spacing_mm: float | None
    uploaded_at: datetime


class AnalysisOut(ORM):
    id: int
    case_id: int
    image_id: int
    status: str
    overall_severity: str | None
    stenosis_detected: bool
    n_stenoses: int
    max_narrowing_pct: float
    confidence: float
    processing_ms: float
    model_versions: dict
    error: str | None
    created_at: datetime


class AnalysisDetail(AnalysisOut):
    result: dict


class AlertOut(ORM):
    id: int
    case_id: int | None
    analysis_id: int | None
    level: str
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime
