'''Schemas'''
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Valid roles for conversation messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ── Message schemas ───────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    role: MessageRole
    content: str = Field(..., min_length=1)
    token_count: Optional[int] = None


class MessageResponse(BaseModel):
    """Schema for returning a message."""
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    token_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Session schemas ───────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    user_id: UUID
    title: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for returning a session."""
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── History schemas ───────────────────────────────────────────────────────────

class HistoryResponse(BaseModel):
    """Schema for returning conversation history."""
    session_id: UUID
    messages: list[MessageResponse]
    total: int


class SaveMessageRequest(BaseModel):
    """Schema for saving a message to a session."""
    session_id: UUID
    role: MessageRole
    content: str = Field(..., min_length=1)
    token_count: Optional[int] = None


class GetHistoryRequest(BaseModel):
    """Schema for requesting conversation history."""
    session_id: UUID
    limit: Optional[int] = Field(default=20, ge=1, le=100)
