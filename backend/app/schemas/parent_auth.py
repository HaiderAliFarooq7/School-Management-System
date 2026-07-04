from pydantic import BaseModel, Field


class ParentLoginRequest(BaseModel):
    mobile_number: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=1, max_length=128)


class ParentTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    parent_name: str | None = None
    mobile_number: str
    must_change_password: bool = False


class ParentChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class DeviceRegisterRequest(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=255)
    platform: str = "android"
