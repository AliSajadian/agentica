from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SearchType(str, Enum):
    """Type of search to perform."""
    web = "web"
    news = "news"
    images = "images"


class SafeSearch(str, Enum):
    """Safe search level."""
    strict = "strict"
    moderate = "moderate"
    off = "off"


# ── Search request/response ───────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Schema for web search request."""
    query: str = Field(..., min_length=2, description="Search query")
    count: int = Field(default=10, ge=1, le=20, description="Number of results")
    search_type: SearchType = Field(default=SearchType.web)
    safe_search: SafeSearch = Field(default=SafeSearch.moderate)
    country: Optional[str] = Field(None, description="Country code e.g. US, GB")
    language: Optional[str] = Field(None, description="Language code e.g. en, fr")


class SearchResult(BaseModel):
    """Single search result item."""
    title: str
    url: str
    description: str
    source: Optional[str] = None
    published_date: Optional[str] = None


class SearchResponse(BaseModel):
    """Full search response with results list."""
    query: str
    total_results: int
    results: list[SearchResult]
    search_type: str
    cached: bool = False


# ── News search ───────────────────────────────────────────────────────────────

class NewsRequest(BaseModel):
    """Schema for news search request."""
    query: str = Field(..., min_length=2)
    count: int = Field(default=10, ge=1, le=20)
    country: Optional[str] = None
    language: Optional[str] = Field(default="en")


class NewsResult(BaseModel):
    """Single news article result."""
    title: str
    url: str
    description: str
    source: str
    published_date: Optional[str] = None
    thumbnail: Optional[str] = None


class NewsResponse(BaseModel):
    """Full news search response."""
    query: str
    total_results: int
    results: list[NewsResult]
    cached: bool = False


# ── Summary (for agent-service) ───────────────────────────────────────────────

class SearchSummaryRequest(BaseModel):
    """Schema for natural language search summary request."""
    query: str = Field(..., min_length=2)
    count: int = Field(default=5, ge=1, le=10)
    search_type: SearchType = Field(default=SearchType.web)


class SearchSummaryResponse(BaseModel):
    """Natural language search summary for agent consumption."""
    query: str
    summary: str
    results: list[SearchResult]
    total: int
