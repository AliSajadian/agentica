# LLM Service

A FastAPI microservice that provides LLM inference capabilities via Ollama.
Part of the [Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The LLM service is the inference layer of the Agentica platform. It wraps a locally running
Ollama instance and exposes three endpoints covering three distinct use cases:

- **`/complete`** — single prompt, direct LLM response (no memory, no context)
- **`/chat`** — multi-turn conversation with message history
- **`/chat/rag`** — RAG-powered chat — receives pre-retrieved context chunks from
  `rag-service` and grounds the LLM answer in your documents

The service never fetches data from the internet at inference time. All knowledge either
comes from the model's pretrained weights or from context chunks injected by the caller.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| LLM Runtime | Ollama |
| Model | llama3.2:3b (3B parameters, CPU inference) |
| Validation | Pydantic v2 |
| HTTP Client | httpx (async) |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- Ollama running with `llama3.2:3b` pulled

---

## Getting Started

### 1. Start Ollama and pull the model

```bash
# start ollama container
docker run -d -p 11434:11434 ollama/ollama

# pull a lightweight model (approx 2GB)
docker exec -it <container_id> ollama pull llama3.2:3b

# verify model is available
docker exec -it <container_id> ollama list
```

### 2. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8002
```

### 3. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build llm-service
```

Swagger UI available at `http://localhost:8002/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/complete` | Single prompt completion |
| POST | `/api/v1/chat` | Multi-turn conversation |
| POST | `/api/v1/chat/rag` | RAG-powered chat with context chunks |
| GET | `/health` | Health check including Ollama status |

---

## Endpoint Reference

### `POST /api/v1/complete`

Direct prompt completion — pure LLM call with no retrieval or memory.
The model answers from its pretrained knowledge only.

**Request:**
```json
{
  "prompt": "What is FastAPI and why is it popular for building APIs?",
  "stream": false
}
```

**Response:**
```json
{
  "prompt": "What is FastAPI and why is it popular for building APIs?",
  "answer": "FastAPI is a modern Python web framework...",
  "model": "llama3.2:3b"
}
```

**What happens behind the curtain:**

```
1. FastAPI validates prompt via CompleteRequest (Pydantic)
2. OllamaClient.generate() sends HTTP POST to Ollama /api/generate
3. llama3.2:3b processes the prompt using its 3B pretrained parameters
4. Model generates tokens one by one (influenced by temperature, top_p)
5. Ollama returns full text → wrapped in CompleteResponse → returned to caller
```

> **Note:** `/complete` has no access to Qdrant, no RAG, no vector search.
> The model may hallucinate on topics outside its training data.
> Use `/chat/rag` when accuracy on your documents matters.

---

### `POST /api/v1/chat`

Multi-turn conversation endpoint. Accepts a full message history so the model
maintains context across turns.

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the difference between LangChain and LangGraph?"
    }
  ],
  "stream": false
}
```

**Response:**
```json
{
  "answer": "LangChain is a framework for building LLM-powered applications...",
  "model": "llama3.2:3b"
}
```

**Multi-turn example:**
```json
{
  "messages": [
    {"role": "user",      "content": "What is LangGraph?"},
    {"role": "assistant", "content": "LangGraph is a library for stateful LLM apps."},
    {"role": "user",      "content": "Can you give me an example?"}
  ],
  "stream": false
}
```

**What happens behind the curtain:**

```
1. FastAPI validates messages list (role must be user/assistant/system)
2. Messages converted to Ollama chat format
3. HTTP POST to Ollama /api/chat — full history sent in one request
4. Model processes all messages as a conversation thread
5. Returns next assistant message
```

> **Key difference from `/complete`:** The model sees all previous messages
> and understands it is in a dialogue, producing contextually aware responses.

---

### `POST /api/v1/chat/rag`

RAG-powered chat. Receives a question plus pre-retrieved context chunks
from `rag-service`. The model is instructed to answer only from the provided context.

**Request:**
```json
{
  "question": "What is LangGraph used for?",
  "context_chunks": [
    {
      "text": "LangGraph is a library for building stateful multi-actor applications with LLMs.",
      "score": 0.92,
      "metadata": {"source": "langgraph_docs.txt"},
      "chunk_index": 0
    }
  ],
  "stream": false,
  "system_prompt": null
}
```

**Response:**
```json
{
  "question": "What is LangGraph used for?",
  "answer": "Based on the provided documentation, LangGraph is used for...",
  "model": "llama3.2:3b",
  "context_used": 1
}
```

**What happens behind the curtain:**

```
1. FastAPI validates RAGRequest (question + context_chunks)
2. PromptBuilder constructs system message:
   - Default or custom system_prompt
   - All context chunks formatted with source + score
3. User question appended as final message
4. Full message list sent to Ollama /api/chat
5. Model generates answer grounded in the provided context
6. Returns answer + context_used count
```

**The RAG chain (called by rag-service):**

```
rag-service /query
    → embed question (FastEmbed)
    → search Qdrant (top-k chunks)
    → POST /api/v1/chat/rag (question + chunks)
    → return grounded answer to user
```

> **Why RAG?** `/complete` and `/chat` can hallucinate because they rely solely
> on pretrained weights. `/chat/rag` grounds the model in your actual documents,
> making answers accurate and verifiable.

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "llm-service",
  "env": "development",
  "ollama": "connected",
  "model": "llama3.2:3b"
}
```

---

## Streaming

All endpoints support streaming responses. Set `"stream": true` to receive
tokens as they are generated (server-sent events style):

```bash
curl -X POST http://localhost:8002/api/v1/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain Kubernetes in simple terms.", "stream": true}'
```

Tokens stream back as plain text chunks in real time.

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
APP_NAME=llm-service
APP_ENV=development
APP_PORT=8002

OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=120

MAX_TOKENS=1024
TEMPERATURE=0.7
TOP_P=0.9
STREAM=true

RAG_SERVICE_URL=http://localhost:8001
LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | llama3.2:3b | Model to use for inference |
| `OLLAMA_TIMEOUT` | 120 | Request timeout in seconds (CPU inference is slow) |
| `TEMPERATURE` | 0.7 | Higher = more creative, lower = more deterministic |
| `TOP_P` | 0.9 | Nucleus sampling threshold |
| `MAX_TOKENS` | 1024 | Maximum tokens per response |

> **CPU inference note:** On a machine without a dedicated GPU, expect
> 1–3 minutes per response with `llama3.2:3b`. This is normal.
> The service automatically falls back to CPU when no CUDA-capable GPU is detected.

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock the Ollama client — no running Ollama instance required for the test suite.

**Test coverage:**
- `/complete` — valid prompt, short prompt rejection, ollama call assertion
- `/chat` — single message, multi-turn history, message order verification
- `/chat/rag` — with context, empty context, custom system prompt
- `/health` — ollama connected, ollama unreachable

---

## GPU Support

The service runs on CPU by default (Intel/AMD integrated graphics). To enable
GPU acceleration on an NVIDIA card:

```python
# In core/ollama.py — add to docker compose environment:
# OLLAMA_NUM_GPU=1
```

Or in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

With a GPU, inference drops from minutes to seconds per response.

---

## Project Structure

```
llm-service/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py             # FastAPI app, lifespan, middleware
│   ├── config.py           # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py     # /chat and /chat/rag endpoints
│   │       └── complete.py # /complete endpoint
│   ├── core/
│   │   └── ollama.py       # Async Ollama HTTP client
│   ├── services/
│   │   └── prompt_builder.py  # RAG prompt construction
│   ├── models/
│   │   └── schemas.py      # Pydantic request/response models
│   └── utils/
│       └── logger.py       # Structlog setup
└── tests/
    ├── conftest.py
    └── test_chat.py
```

---

## Part of Agentica

This service is one component of the Agentica platform:

```
gateway-service  →  rag-service  →  llm-service  ←  agent-service
                                         ↑
                                    memory-service
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT