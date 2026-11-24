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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"