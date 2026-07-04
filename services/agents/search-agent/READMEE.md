# Search Agent

A FastAPI microservice that provides real-time web and news search capabilities.
Part of the [Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The search agent gives the Agentica platform access to real-time information beyond the
LLM's training data cutoff. It exposes three endpoints — web search, news search, and a
natural language summary endpoint designed for consumption by `agent-service`.

Search results are cached in Redis to avoid redundant API calls and reduce latency on
repeated queries.

### Supported providers

| Provider | Status | Notes |
|---|---|---|
| DuckDuckGo | ✅ Active | No API key required, uses `duckduckgo-search` library |
| Brave Search | ⚙ Supported | Requires API key — blocked from some regions |
| Tavily | ⚙ Supported | 1000 free searches/month — blocked from some regions |

> **Regional note:** Brave and Tavily APIs return `403 Forbidden` from certain regions
> due to access restrictions. DuckDuckGo is used as the default provider and works
> without any API key or registration.
> To switch providers, update `core/brave.py` — the interface is identical across all three.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Search Provider | DuckDuckGo (`duckduckgo-search`) |
| Cache | Redis |
| HTTP Client | httpx (async) |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- Redis running

---

## Getting Started

### 1. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8012
```

### 3. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build search-agent
```

Swagger UI available at `http://localhost:8012/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/search/web` | Web search |
| POST | `/api/v1/search/news` | News search |
| POST | `/api/v1/search/summary` | Natural language summary for agent-service |
| GET | `/health` | Health check including search API status |

---

## Endpoint Reference

### `POST /api/v1/search/web`

Search the web for a query and return a list of relevant results.

**Request:**
```json
{
  "query": "latest developments in LangGraph 2026",
  "count": 5,
  "search_type": "web",
  "safe_search": "moderate",
  "country": "US",
  "language": "en"
}
```

**Response:**
```json
{
  "query": "latest developments in LangGraph 2026",
  "total_results": 5,
  "results": [
    {
      "title": "LangGraph v1.0 Released",
      "url": "https://blog.langchain.dev/langgraph-v1",
      "description": "LangGraph reaches stable 1.0 with improved state management...",
      "source": "LangChain Blog",
      "published_date": null
    }
  ],
  "search_type": "web",
  "cached": false
}
```

**What happens behind the curtain:**

```
1. FastAPI validates SearchRequest (Pydantic)
2. Check Redis cache (key: search:web:{query}:{count})
   → cache hit  → return cached results instantly
   → cache miss → call DuckDuckGo via duckduckgo-search library
3. Parse raw results into SearchResult list
4. Store in Redis with TTL (default 5 minutes)
5. Return SearchResponse
```

---

### `POST /api/v1/search/news`

Search for recent news articles on a topic.
Internally appends `"news"` to the query for better news-specific results.

**Request:**
```json
{
  "query": "artificial intelligence regulation",
  "count": 10,
  "country": "US",
  "language": "en"
}
```

**Response:**
```json
{
  "query": "artificial intelligence regulation",
  "total_results": 8,
  "results": [
    {
      "title": "EU AI Act comes into full effect",
      "url": "https://example.com/eu-ai-act",
      "description": "The European Union's landmark AI regulation...",
      "source": "DuckDuckGo",
      "published_date": "2026-06-01",
      "thumbnail": null
    }
  ],
  "cached": false
}
```

---

### `POST /api/v1/search/summary`

Search and return a natural language summary of the top results.
This endpoint is designed to be called by `agent-service` — it returns
both the structured results and a pre-formatted summary string ready
to inject into an LLM prompt.

**Request:**
```json
{
  "query": "how does RAG work in LLM applications",
  "count": 5,
  "search_type": "web"
}
```

**Response:**
```json
{
  "query": "how does RAG work in LLM applications",
  "summary": "Top results for 'how does RAG work in LLM applications':\n1. RAG Explained — Retrieval-Augmented Generation combines... (https://...)\n2. ...",
  "results": [...],
  "total": 5
}
```

The `summary` field is formatted as a numbered list of top 3 results with
title, truncated description, and URL — ready to pass directly to an LLM as context.

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "search-agent",
  "env": "development",
  "search_api": "connected",
  "provider": "DuckDuckGo"
}
```

---

## Switching Search Providers

The search client interface is identical across all providers.
To switch, update `app/core/brave.py`:

### DuckDuckGo (default, no key needed)

```python
from duckduckgo_search import DDGS

class DuckDuckGoClient:
    async def search(self, query: str, count: int = 10) -> list[dict]:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=count))
```

### Brave Search

```python
# requires: BRAVE_API_KEY in .env
# pip install httpx

headers = {"X-Subscription-Token": settings.BRAVE_API_KEY}
params  = {"q": query, "count": count}
response = await client.get(
    "https://api.search.brave.com/res/v1/web/search",
    headers=headers, params=params
)
```

### Tavily

```python
# requires: TAVILY_API_KEY in .env
# pip install tavily-python

from tavily import TavilyClient
client = TavilyClient(api_key=settings.TAVILY_API_KEY)
results = client.search(query=query, max_results=count)
```

---

## Redis Cache Strategy

```
search request
    → build cache key: search:{type}:{query}:{count}
    → check Redis
        → hit  → return immediately (cached: true)
        → miss → call search provider → parse → store with TTL → return
```

**Cache TTL:** 300 seconds (5 minutes) by default — configurable via `SEARCH_CACHE_TTL`.
Short TTL ensures news results stay fresh while avoiding redundant API calls.

---

## Configuration

Copy `.env.example` to `.env`:

```env
APP_NAME=search-agent
APP_ENV=development
APP_PORT=8012

# Active provider: DuckDuckGo (no key needed)
# BRAVE_API_KEY=your-brave-api-key
# TAVILY_API_KEY=your-tavily-api-key

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=3
SEARCH_CACHE_TTL=300

LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `SEARCH_CACHE_TTL` | 300 | Cache TTL in seconds |
| `BRAVE_API_KEY` | — | Brave Search API key (optional) |
| `TAVILY_API_KEY` | — | Tavily API key (optional) |
| `REDIS_DB` | 3 | Redis database index (isolated per service) |

---

## Project Structure

```
search-agent/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py               # FastAPI app, lifespan, health check
│   ├── config.py             # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       └── search.py     # /web, /news, /summary endpoints
│   ├── core/
│   │   └── brave.py          # Search client (DuckDuckGo/Brave/Tavily)
│   ├── services/
│   │   └── search.py         # Business logic, caching, result parsing
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response schemas
│   └── utils/
│       └── logger.py         # Structlog setup
└── tests/
    ├── conftest.py
    └── test_search.py
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock the search client — no internet connection or API key required.

---

## Part of Agentica

```
gateway-service
    → agent-service
        → search-agent  ← you are here
            → DuckDuckGo / Brave / Tavily (external)
            → Redis (cache)
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT