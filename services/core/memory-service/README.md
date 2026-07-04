# Memory Service

A FastAPI microservice that manages conversation sessions and message history for the
[Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The memory service is the stateful backbone of the Agentica platform. Without it, every
message sent to the LLM is isolated — the model has no awareness of what was said before.
The memory service solves this by storing conversation history in PostgreSQL and caching
recent sessions in Redis for fast retrieval.

Every conversation has a `session_id`. Each message (user or assistant) is saved with its
role, content, and token count. When a new message arrives, the memory service returns the
last N messages as context to inject into the LLM prompt.

**Storage strategy:**
- **PostgreSQL** — persistent storage for all sessions and messages
- **Redis** — cache layer for recent session history (TTL-based, invalidated on new message)

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic |
| Cache | Redis |
| Async Driver | asyncpg |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- PostgreSQL running
- Redis running

---

## Getting Started

### 1. Start dependencies

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=agentica \
  -e POSTGRES_PASSWORD=agentica \
  -e POSTGRES_DB=agentica_memory \
  postgres:16-alpine

docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8003
```

### 3. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build memory-service
```

Swagger UI available at `http://localhost:8003/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sessions` | Create a new conversation session |
| GET | `/api/v1/sessions/{session_id}` | Get session by ID |
| DELETE | `/api/v1/sessions/{session_id}` | Delete session and all its messages |
| GET | `/api/v1/sessions/user/{user_id}` | Get all sessions for a user |
| POST | `/api/v1/sessions/messages` | Save a message to a session |
| POST | `/api/v1/sessions/history` | Get conversation history (Redis-cached) |
| DELETE | `/api/v1/sessions/{session_id}/history` | Clear messages without deleting session |
| GET | `/health` | Health check including Redis status |
| GET | `/ready` | Readiness probe for Kubernetes |

---

## Endpoint Reference

### `POST /api/v1/sessions`

Create a new conversation session for a user.

**Request:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Trip planning to Paris"
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Trip planning to Paris",
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T10:00:00Z"
}
```

---

### `GET /api/v1/sessions/{session_id}`

Retrieve a session by its UUID.

**Response:** `SessionResponse` or `404` if not found.

---

### `DELETE /api/v1/sessions/{session_id}`

Delete a session and all its messages (cascade delete).
Also invalidates the Redis cache for this session.

**Response:**
```json
{"message": "Session deleted successfully"}
```

---

### `GET /api/v1/sessions/user/{user_id}`

Retrieve all sessions belonging to a user, ordered by most recently updated.

**Response:** Array of `SessionResponse` objects.

---

### `POST /api/v1/sessions/messages`

Save a single message (user or assistant) to a session.
Automatically invalidates the Redis cache so the next history fetch is fresh.

**Request:**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "user",
  "content": "What is the weather in Paris next weekend?",
  "token_count": 12
}
```

**Response:**
```json
{
  "id": "msg-uuid-here",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "user",
  "content": "What is the weather in Paris next weekend?",
  "token_count": 12,
  "created_at": "2026-06-01T10:01:00Z"
}
```

**Valid roles:** `user`, `assistant`, `system`, `tool`

---

### `POST /api/v1/sessions/history`

Retrieve conversation history for a session with Redis caching.

**Request:**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "limit": 20
}
```

**Response:**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "messages": [
    {
      "id": "msg-uuid-1",
      "session_id": "a1b2c3d4-...",
      "role": "user",
      "content": "What is the weather in Paris?",
      "token_count": 8,
      "created_at": "2026-06-01T10:01:00Z"
    },
    {
      "id": "msg-uuid-2",
      "session_id": "a1b2c3d4-...",
      "role": "assistant",
      "content": "The weather in Paris is currently 18°C and sunny.",
      "token_count": 14,
      "created_at": "2026-06-01T10:01:05Z"
    }
  ],
  "total": 2
}
```

**Cache strategy:**

```
get_history request
    → check Redis (key: session:{session_id})
        → cache hit  → return cached messages (fast)
        → cache miss → query PostgreSQL → cache result → return
save_message request
    → write to PostgreSQL
    → delete Redis cache key (force fresh fetch next time)
```

---

### `DELETE /api/v1/sessions/{session_id}/history`

Clear all messages in a session without deleting the session itself.
Useful for starting a fresh conversation while preserving the session metadata.

**Response:**
```json
{"message": "History cleared successfully"}
```

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "memory-service",
  "env": "development",
  "redis": "connected"
}
```

---

### `GET /ready`

Kubernetes readiness probe — returns `200` when the service is ready to accept traffic
(database initialized, Redis reachable).

```json
{"status": "ready"}
```

---

## How It Works

### Session lifecycle

```
1. gateway-service creates a session on first user message
      → POST /api/v1/sessions → returns session_id

2. agent-service saves each turn
      → POST /api/v1/sessions/messages (role: user,    content: question)
      → POST /api/v1/sessions/messages (role: assistant, content: answer)

3. Before each LLM call, agent-service fetches history
      → POST /api/v1/sessions/history → inject into LLM context

4. User can delete session or clear history at any time
```

### Redis cache invalidation

```
write message → invalidate cache key
read history  → check cache first
               → on miss: fetch PostgreSQL, populate cache with TTL
```

This means the first read after a write always hits PostgreSQL (fresh),
subsequent reads within the TTL window hit Redis (fast).

---

## Database Schema

### `sessions` table

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Session identifier |
| user_id | UUID | Owner of the session |
| title | VARCHAR(500) | Optional session title |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

### `messages` table

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Message identifier |
| session_id | UUID (FK) | Parent session (cascade delete) |
| role | VARCHAR(50) | user / assistant / system / tool |
| content | TEXT | Message content |
| token_count | INTEGER | Optional token count for cost tracking |
| created_at | TIMESTAMPTZ | Creation timestamp |

Tables are created automatically on startup via SQLAlchemy `create_all`.
Alembic is configured for schema migrations in production.

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
APP_NAME=memory-service
APP_ENV=development
APP_PORT=8003

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=agentica
POSTGRES_PASSWORD=agentica
POSTGRES_DB=agentica_memory
DATABASE_URL=postgresql+asyncpg://agentica:agentica@localhost:5432/agentica_memory

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=3600

MAX_HISTORY_MESSAGES=20
SESSION_TTL_HOURS=24

LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `REDIS_TTL` | 3600 | Cache TTL in seconds (1 hour) |
| `MAX_HISTORY_MESSAGES` | 20 | Max messages returned per history request |
| `SESSION_TTL_HOURS` | 24 | Session expiry (future cleanup job) |

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock both the database session and Redis cache — no running PostgreSQL or Redis required.

**Test coverage:**
- `POST /sessions` — create session, verify memory service called
- `GET /sessions/{id}` — found, not found (404)
- `GET /sessions/user/{user_id}` — returns list
- `POST /sessions/messages` — user message, assistant message, call assertions
- `POST /sessions/history` — with messages, empty session, limit verification
- `DELETE /sessions/{id}` — delete called, success message
- `DELETE /sessions/{id}/history` — clear called, success message
- `GET /health` — redis connected, redis unreachable

---

## Project Structure

```
memory-service/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                 # FastAPI app, lifespan, db init
│   ├── config.py               # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       └── sessions.py     # All session + message endpoints
│   ├── core/
│   │   └── cache.py            # Redis cache client
│   ├── db/
│   │   ├── base.py             # Engine, session factory, UuidPk type
│   │   ├── models.py           # Session + Message SQLAlchemy models
│   │   └── migrations/         # Alembic migrations
│   ├── services/
│   │   └── memory.py           # Business logic — CRUD + cache strategy
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response schemas
│   └── utils/
│       └── logger.py           # Structlog setup
└── tests/
    ├── conftest.py
    └── test_sessions.py
```

---

## Part of Agentica

```
gateway-service
    → agent-service
        → memory-service  ← saves every user + assistant message
        → llm-service     ← receives history as context
        → rag-service
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT