from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.case import CaseStatus
from app.schemas.case_image import CaseImageRead


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    patient_id: int | None = None


class CaseUpdate(BaseModel):
    """All fields optional: PATCH changes only what the client sends."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: CaseStatus | None = None
    patient_id: int | None = None

    @field_validator("title", "status")
    @classmethod
    def must_not_be_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: CaseStatus
    patient_id: int | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseRead):
    images: list[CaseImageRead] = []


class CaseList(BaseModel):
    items: list[CaseRead]
    total: int
    skip: int
    limit: int