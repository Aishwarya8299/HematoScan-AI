"""Authentication request, token, and user models."""

from enum import Enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    """Roles allowed to access the Hematoscan portal."""

    TECHNICIAN = "technician"
    DOCTOR = "doctor"


class TokenResponse(BaseModel):
    """Bearer token returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds.")


class LoginRequest(BaseModel):
    """Credentials submitted by a portal user."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    """Professional account details submitted during registration."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=120)
    role: UserRole


class MessageResponse(BaseModel):
    """Simple acknowledgement returned by session operations."""

    message: str


class TokenPayload(BaseModel):
    """Validated claims extracted from an access token."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    subject: str = Field(alias="sub")
    role: UserRole
    token_id: str = Field(alias="jti")
    expires_at: datetime = Field(alias="exp")


class UserPublic(BaseModel):
    """Safe user representation returned by authenticated endpoints."""

    id: str
    email: str
    role: UserRole
    display_name: str
