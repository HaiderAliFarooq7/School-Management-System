from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)
    role_name: str
    assigned_class_name: str | None = None


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    role_name: str | None = None
    assigned_class_name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    user_id: int
    username: str
    full_name: str
    role_name: str
    assigned_class_name: str | None = None
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
