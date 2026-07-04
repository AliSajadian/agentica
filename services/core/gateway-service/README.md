# Gateway Service

A FastAPI microservice that serves as the single entry point for the
[Agentica](https://github.com/yourusername/agentica) agentic AI platform.
Handles authentication, JWT token management, rate limiting, and request proxying
to upstream services.

---

## Overview

The gateway service is the front door of the Agentica platform. No upstream service
is exposed directly to clients — all traffic flows through the gateway, which:

- **Authenticates** every request via JWT bearer tokens
- **Rate limits** per user per endpoint using Redis
- **Routes** authenticated requests to the correct upstream service
- **Injects** the authenticated user's ID into forwarded requests via `X-User-ID` header
- **Reports** health status of all upstream services in one call

Upstream services trust the `X-User-ID` header injected by the gateway — they do not
perform their own authentication.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic |
| Cache / Rate Limiting | Redis |
| HTTP Client | httpx (async) |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- PostgreSQL running
- Redis running
- Upstream services running (rag, llm, memory, agent)

---

## Getting Started

### 1. Start dependencies

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=agentica \
  -e POSTGRES_PASSWORD=agentica \
  -e POSTGRES_DB=agentica_gateway \
  postgres:16-alpine

docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

### 3. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build gateway-service
```

Swagger UI available at `http://localhost:8000/docs`.

---

## API Endpoints

### Auth

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user | No |
| POST | `/api/v1/auth/login` | Login and get JWT tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |

### Proxy

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/api/v1/proxy/rag/{path}` | Proxy to rag-service | Yes |
| POST | `/api/v1/proxy/llm/{path}` | Proxy to llm-service | Yes |
| POST | `/api/v1/proxy/memory/{path}` | Proxy to memory-service | Yes |
| POST | `/api/v1/proxy/agent/{path}` | Proxy to agent-service | Yes |
| GET | `/api/v1/proxy/health/upstream` | Health of all upstream services | Yes |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check including Redis and upstream status |
| GET | `/ready` | Readiness probe for Kubernetes |

---

## Endpoint Reference

### `POST /api/v1/auth/register`

Register a new user account. Email must be unique.

**Request:**
```json
{
  "email": "ali@example.com",
  "password": "securepassword123",
  "full_name": "Ali Ahmadi"
}
```

**Response:** `UserResponse` with UUID, email, role, and timestamps.

**Errors:** `409 Conflict` if email already registered.

---

### `POST /api/v1/auth/login`

Authenticate with email and password. Returns a short-lived access token
and a long-lived refresh token.

**Request:**
```json
{
  "email": "ali@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:** `401 Unauthorized` for invalid credentials, `403 Forbidden` if account disabled.

---

### `POST /api/v1/auth/refresh`

Exchange a valid refresh token for a new access token + refresh token pair.
The old refresh token is revoked on use (token rotation).

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** New `TokenResponse` with fresh access + refresh tokens.

**Errors:** `401 Unauthorized` if refresh token is expired or revoked.

---

### `GET /api/v1/auth/me`

Returns the currently authenticated user's profile.
Requires `Authorization: Bearer <access_token>` header.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "ali@example.com",
  "full_name": "Ali Ahmadi",
  "role": "user",
  "is_active": true,
  "created_at": "2026-06-01T10:00:00Z"
}
```

---

### `POST /api/v1/proxy/rag/{path}`

Forward an authenticated request to rag-service.
Rate limiting applied per user per path.
`X-User-ID` header injected for downstream identification.

**Example — ingest a document:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/rag/ingest \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "LangGraph is a stateful LLM framework.", "source": "docs.txt"}'
```

**Example — semantic search:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/rag/search \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is LangGraph?", "top_k": 5}'
```

The `{path}` is appended to `/api/v1/` on the upstream service. So
`/api/v1/proxy/rag/ingest` → `rag-service:8001/api/v1/ingest`.

---

### `POST /api/v1/proxy/llm/{path}`

Forward an authenticated request to llm-service.

**Example — chat:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/llm/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is FastAPI?"}], "stream": false}'
```

---

### `POST /api/v1/proxy/memory/{path}`

Forward an authenticated request to memory-service.

**Example — create a session:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/memory/sessions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-...", "title": "My conversation"}'
```

---

### `POST /api/v1/proxy/agent/{path}`

Forward an authenticated request to agent-service.

**Example — run an agent task:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/agent/run \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"task": "Search the docs for LangGraph state management", "session_id": "..."}'
```

---

### `GET /api/v1/proxy/health/upstream`

Returns health status of all registered upstream services.
Requires authentication.

**Response:**
```json
{
  "rag": "ok",
  "llm": "ok",
  "memory": "ok",
  "agent": "ok"
}
```

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "gateway-service",
  "env": "development",
  "redis": "connected",
  "upstream": {
    "rag": "ok",
    "llm": "ok",
    "memory": "ok",
    "agent": "ok"
  }
}
```

---

### `GET /ready`

Kubernetes readiness probe.

```json
{"status": "ready"}
```

---

## How It Works

### Request flow

```
Client
  │
  ▼
POST /api/v1/proxy/rag/search
  │
  ├── 1. Extract JWT from Authorization header
  ├── 2. Decode + validate token (jose)
  ├── 3. Check token type = "access"
  ├── 4. Rate limit check (Redis INCR per user per path)
  ├── 5. Forward request to rag-service:8001/api/v1/search
  │        with X-User-ID: <user_uuid> header injected
  ├── 6. Return upstream response to client
  └── Errors: 401 (bad token), 429 (rate limit), 502 (upstream down), 504 (timeout)
```

### Token lifecycle

```
Register → hashed password stored in PostgreSQL
Login    → access token (30min) + refresh token (7 days) issued
           refresh token hash stored in refresh_tokens table
Request  → access token validated on every request
Refresh  → old refresh token revoked, new pair issued (token rotation)
```

### Rate limiting

Rate limiting uses Redis `INCR` with TTL:

```
Key: ratelimit:{user_id}:{endpoint}
On request: INCR key → if count > MAX_REQUESTS → 429
On first request: SET TTL = WINDOW_SECONDS
```

Default: 100 requests per 60 seconds per user per endpoint.
If Redis is unavailable, the rate limiter fails open (requests pass through).

---

## Database Schema

### `users` table

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | User identifier |
| email | VARCHAR(255) | Unique email address |
| hashed_password | VARCHAR(255) | bcrypt hashed password |
| full_name | VARCHAR(255) | Display name |
| role | VARCHAR(50) | user / admin / readonly |
| is_active | BOOLEAN | Account enabled flag |
| created_at | TIMESTAMPTZ | Registration timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

### `refresh_tokens` table

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Token record identifier |
| user_id | UUID | Owner of the token |
| token_hash | VARCHAR(255) | SHA-256 hash of the refresh token |
| is_revoked | BOOLEAN | Revocation flag |
| expires_at | TIMESTAMPTZ | Token expiry |
| created_at | TIMESTAMPTZ | Issuance timestamp |

---

## Configuration

Copy `.env.example` to `.env`:

```env
APP_NAME=gateway-service
APP_ENV=development
APP_PORT=8000

JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=agentica
POSTGRES_PASSWORD=agentica
POSTGRES_DB=agentica_gateway
DATABASE_URL=postgresql+asyncpg://agentica:agentica@localhost:5432/agentica_gateway

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

RAG_SERVICE_URL=http://localhost:8001
LLM_SERVICE_URL=http://localhost:8002
MEMORY_SERVICE_URL=http://localhost:8003
AGENT_SERVICE_URL=http://localhost:8004

LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET_KEY` | — | **Change in production** — signs all tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `RATE_LIMIT_REQUESTS` | 100 | Max requests per window per user |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate limit window in seconds |

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock the database session, Redis, and upstream service calls.

---

## Project Structure

```
gateway-service/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                    # FastAPI app, lifespan, middleware
│   ├── config.py                  # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py            # Register, login, refresh, me endpoints
│   │       └── proxy.py           # Proxy endpoints for all upstream services
│   ├── core/
│   │   ├── security.py            # JWT creation, validation, password hashing
│   │   └── rate_limiter.py        # Redis-based per-user rate limiting
│   ├── db/
│   │   ├── base.py                # Engine, session factory, UuidPk type
│   │   └── models.py              # User + RefreshToken SQLAlchemy models
│   ├── services/
│   │   ├── auth.py                # User registration, login, token management
│   │   └── proxy.py               # HTTP forwarding logic, upstream health checks
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response schemas
│   └── utils/
│       └── logger.py              # Structlog setup
└── tests/
    ├── conftest.py
    └── test_auth.py
```

---

## Part of Agentica

```
Client
  ↓
gateway-service  ← you are here (port 8000)
  ├── → rag-service     (port 8001)
  ├── → llm-service     (port 8002)
  ├── → memory-service  (port 8003)
  └── → agent-service   (port 8004)
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT