from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    uploaded_by_id: int
    original_filename: str
    file_size: int
    sha256: str
    created_at: datetime