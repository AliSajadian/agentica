'''Schemas'''
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MessageRole(str, Enum):
    '''Message Role'''
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    '''Message'''
    role: MessageRole
    content: str


# ── Complete (single prompt) ──────────────────────────────────────────────────

class CompleteRequest(BaseModel):
    '''Complete Request'''
    prompt: str = Field(..., min_length=5)
    stream: bool = Field(default=False)


class CompleteResponse(BaseModel):
    '''Complete Response'''
    prompt: str
    answer: str
    model: str


# ── Chat (message history) ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    '''Chat Request'''
    messages: list[Message] = Field(..., min_length=1)
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    '''Chat Response'''
    answer: str
    model: str


# ── RAG Query (question + context from rag-service) ──────────────────────────

class ContextChunk(BaseModel):
    '''Context Chunk'''
    text: str
    score: float
    metadata: dict
    chunk_index: int


class RAGRequest(BaseModel):
    '''RAG Request'''
    question: str = Field(..., min_length=5)
    context_chunks: list[ContextChunk]
    stream: bool = Field(default=False)
    system_prompt: Optional[str] = None


class RAGResponse(BaseModel):
    '''RAG Response'''
    question: str
    answer: str
    model: str
    context_used: int
