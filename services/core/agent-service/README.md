# Agent Service

A FastAPI microservice that orchestrates multi-step AI agent workflows using LangGraph.
Part of the [Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The agent service is the brain of the Agentica platform. It receives a user task, decomposes
it into steps, calls the appropriate tools (backed by rag-service, llm-service, and
memory-service), and returns a final answer.

Built on **LangGraph**, the orchestration is modeled as a stateful graph where each node
represents an agent action and edges represent transitions based on the result. This enables
complex multi-step reasoning — the agent can decide which tool to call next based on
intermediate results, retry on failure, or combine outputs from multiple tools.

**Service clients:**
- `rag_client.py` — calls rag-service for document search and ingestion
- `llm_client.py` — calls llm-service for LLM inference and RAG-powered answers
- `memory_client.py` — calls memory-service to save/retrieve conversation history

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Agent Orchestration | LangGraph |
| HTTP Clients | httpx (async) |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- rag-service, llm-service, and memory-service running

---

## Getting Started

### 1. Start dependencies

```bash
# from the agentica root
docker compose up rag-service llm-service memory-service
```

### 2. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8004
```

### 3. Run with Docker Compose

```bash
docker compose up --build agent-service
```

Swagger UI available at `http://localhost:8004/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/agent/run` | Run a multi-step agent task |
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe for Kubernetes |

---

## Endpoint Reference

### `POST /api/v1/agent/run`

Submit a task to the agent orchestrator. The agent decomposes the task,
calls the appropriate tools via service clients, and returns a final answer.

**Request:**
```json
{
  "task": "What does the documentation say about LangGraph state management?",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "answer": "According to the ingested documentation, LangGraph manages state by...",
  "steps_taken": 3,
  "tools_used": ["rag_search", "llm_chat_rag"],
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**What happens behind the curtain:**

```
1. FastAPI validates the request
2. Orchestrator initializes LangGraph state with task + session context
3. LangGraph graph starts execution:
   a. base agent decides which tool to call first
   b. tool node executes (e.g. rag_client.search())
   c. result fed back into graph state
   d. agent decides next step or terminates
4. memory_client saves user message + final answer to memory-service
5. Final answer returned to caller
```

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "agent-service",
  "env": "development"
}
```

---

### `GET /ready`

Kubernetes readiness probe — returns `200` when the service is ready to accept traffic.

```json
{"status": "ready"}
```

---

## Architecture

### Project structure

```
agent-service/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                   # FastAPI app, lifespan, middleware
│   ├── config.py                 # Settings via pydantic-settings
│   ├── dependencies.py           # FastAPI dependency injection
│   ├── agents/
│   │   ├── base.py               # Base agent class
│   │   ├── orchestrator.py       # LangGraph orchestration graph
│   │   └── tools/                # Tool definitions wrapping service clients
│   ├── api/
│   │   └── v1/
│   │       └── routes/           # API route handlers
│   ├── clients/
│   │   ├── llm_client.py         # HTTP client for llm-service
│   │   ├── memory_client.py      # HTTP client for memory-service
│   │   └── rag_client.py         # HTTP client for rag-service
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response schemas
│   └── utils/
│       └── logger.py             # Structlog setup
└── tests/
    ├── conftest.py
    └── test_agent.py
```

### Service communication

```
agent-service
    ├── → rag-service  /api/v1/search     (rag_client.py)
    ├── → rag-service  /api/v1/query      (rag_client.py)
    ├── → llm-service  /api/v1/chat       (llm_client.py)
    ├── → llm-service  /api/v1/chat/rag   (llm_client.py)
    └── → memory-service /api/v1/sessions/messages  (memory_client.py)
         → memory-service /api/v1/sessions/history   (memory_client.py)
```

### LangGraph orchestration

```
START
  │
  ▼
[base agent]  ← decides which tool to call based on task
  │
  ├──→ [rag_search tool]    → searches Qdrant via rag-service
  ├──→ [rag_query tool]     → retrieves context + calls llm-service
  ├──→ [llm_chat tool]      → direct LLM conversation
  └──→ [memory tool]        → fetch/save conversation history
  │
  ▼
[orchestrator] ← aggregates results, decides continue or finish
  │
  ▼
END → return final answer
```

---

## Configuration

Copy `.env.example` to `.env`:

```env
APP_NAME=agent-service
APP_ENV=development
APP_PORT=8004

RAG_SERVICE_URL=http://localhost:8001
LLM_SERVICE_URL=http://localhost:8002
MEMORY_SERVICE_URL=http://localhost:8003

LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `RAG_SERVICE_URL` | http://localhost:8001 | RAG service base URL |
| `LLM_SERVICE_URL` | http://localhost:8002 | LLM service base URL |
| `MEMORY_SERVICE_URL` | http://localhost:8003 | Memory service base URL |

In Docker Compose, these point to container names:
```env
RAG_SERVICE_URL=http://rag-service:8001
LLM_SERVICE_URL=http://llm-service:8002
MEMORY_SERVICE_URL=http://memory-service:8003
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock all service clients — no running upstream services required.

---

## Part of Agentica

```
gateway-service
    → agent-service  ← you are here
        → rag-service    (document search)
        → llm-service    (LLM inference)
        → memory-service (conversation history)
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT