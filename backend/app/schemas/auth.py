from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    assigned_class_name: str | None = None
    # Tenant identity for this session (which school the token is pinned to).
    school_id: int | None = None
    school_name: str = ""
    campus_name: str = ""
    is_super: bool = False


class MeResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    role: str
    assigned_class_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
