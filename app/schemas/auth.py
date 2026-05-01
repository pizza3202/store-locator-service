from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class UserCreateRequest(BaseModel):
    user_id: str
    email: EmailStr
    password: str = Field(min_length=12)
    role: str


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime
