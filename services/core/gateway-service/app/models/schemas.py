'''Schemas'''
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


# ── Auth schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


# ── User schemas ──────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Schema for returning user data."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


# ── Token payload ─────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str
    role: UserRole
    exp: int
    type: str


# ── Proxy schemas ─────────────────────────────────────────────────────────────

class ProxyRequest(BaseModel):
    """Schema for proxied requests to upstream services."""
    service: str = Field(..., description="Target service name")
    path: str = Field(..., description="Target path on the service")
    payload: Optional[dict] = None
