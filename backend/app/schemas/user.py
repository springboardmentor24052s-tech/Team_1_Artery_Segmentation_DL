from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=72)  # bcrypt's limit is 72 bytes


class AdminUserCreate(UserCreate):
    role: str


class RoleUpdate(BaseModel):
    role: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None


class LoginAuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    full_name: str | None = None
    user_role: str
    attempted_email_masked: str
    outcome: str
    client_ip: str
    user_agent: str
    request_id: str | None
    created_at: datetime


class UserAuditResponse(BaseModel):
    total_events: int
    active_users: list[UserRead]
    recent_logins: list[LoginAuditEntry]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"