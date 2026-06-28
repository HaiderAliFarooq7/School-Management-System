from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    assigned_class_name: str | None = None


class MeResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    role: str
    assigned_class_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
