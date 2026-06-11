'''Schemas'''
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class AgentRole(str, Enum):
    """Supported agent roles."""

    GENERAL = "general"


class Message(BaseModel):
    """A single conversation message."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentRunRequest(BaseModel):
    """Request payload to run the agent."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(..., description="Session ID from memory-service")
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., min_length=1, description="User message")
    role: AgentRole = Field(default=AgentRole.GENERAL)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    """Response from a completed agent run."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    answer: str
    steps: list[str] = Field(default_factory=list, description="Tool calls made")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """LangGraph state passed between nodes."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_id: str
    message: str
    history: list[Message] = Field(default_factory=list)
    context_chunks: list[str] = Field(default_factory=list)
    answer: str = ""
    steps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
