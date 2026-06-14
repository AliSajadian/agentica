'''Schemas '''
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class DocumentStatus(str, Enum):
    '''Document status enumerarion'''
    PADDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    '''Ingest request'''
    text: str = Field(..., min_length=10, description="Raw text to ingest")
    source: Optional[str] = Field(None, description="Document source/filename")
    metadata: Optional[dict] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    '''Ingest response'''
    document_id: UUID = Field(default_factory=uuid4)
    chunks_created: int
    status: DocumentStatus = DocumentStatus.COMPLETED
    message: str = "Document ingested successfully"


# ── Search ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    '''Search request'''
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata_filter: Optional[dict] = None


class SearchResult(BaseModel):
    '''Search result'''
    text: str
    score: float
    metadata: dict
    chunk_index: int


class SearchResponse(BaseModel):
    '''Search response'''
    query: str
    results: list[SearchResult]
    total: int


# ── Query (RAG) ───────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    '''Query request'''
    question: str = Field(..., min_length=5)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.5)
    metadata_filter: Optional[dict] = None


class QueryResponse(BaseModel):
    '''Query response'''
    question: str
    context_chunks: list[SearchResult]
    total_context: int
    # LLM answer will be added when llm-service is connected
    answer: Optional[str] = None
