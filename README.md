```
# Agentica

A production-grade agentic AI orchestration platform built with FastAPI, Ollama, and Qdrant.
Agentica enables natural language interaction with real-world services — users can check weather,
search the web, and (soon) plan trips, track finances, and manage schedules through a unified AI agent layer.

> Built as a professional portfolio project demonstrating real-world AI engineering,
> microservices architecture, and agentic AI orchestration skills.

---

## Vision

A single user message like:

```
"Plan me a 3-day trip to Paris next weekend, find the cheapest flights from Tehran,
book a hotel near the Eiffel Tower under $100/night,
and tell me what to pack based on the weather forecast."
```

Gets automatically orchestrated across multiple specialized agents:

```
gateway-service (auth + routing)
    → agent-service (orchestrator)
        → travel-agent   (flights + hotels)
        → weather-agent  (Paris forecast)
        → llm-service    (packing suggestions)
        → memory-service (save trip plan)
        → return complete plan to user
```

---

## Architecture

```
agentica/
├── services/
│   ├── core/
│   │   ├── rag-service/        # Document ingestion, embedding, retrieval    (port 8001)
│   │   ├── llm-service/        # LLM inference, RAG-powered chat             (port 8002)
│   │   ├── memory-service/     # Conversation history, session management    (port 8003)
│   │   ├── agent-service/      # Agent orchestration, multi-step reasoning   (port 8004)
│   │   └── gateway-service/    # Auth, routing, rate limiting                (port 8000)
│   └── agents/
│       ├── weather-agent/      # Weather forecasts                          (port 8011)
│       ├── search-agent/       # Web search, real-time information          (port 8012)
│       ├── travel-agent/       # Flights, hotels, trains          [planned] (port 8010)
│       ├── finance-agent/      # Stocks, currency, crypto         [planned] (port 8013)
│       ├── news-agent/         # Latest news                      [planned] (port 8014)
│       ├── calendar-agent/     # Schedule management, reminders   [planned] (port 8015)
│       ├── maps-agent/         # Directions, nearby places        [planned] (port 8016)
│       └── email-agent/        # Send/read emails                 [planned] (port 8017)
├── infra/
│   ├── prometheus.yml
│   ├── grafana/
│   │   └── provisioning/
│   └── k8s/
│       ├── namespace.yml
│       ├── config/              # ConfigMaps, Secrets
│       ├── storage/              # PersistentVolumeClaims
│       ├── infrastructure/       # Qdrant, Ollama, Postgres, Redis, Prometheus, Grafana, Blackbox
│       ├── daemonsets/           # node-exporter, fluent-bit
│       ├── services/             # Deployment + Service per microservice
│       └── ingress/              # Routing rules, strip-prefix middlewares
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Core Platform Services

| Service | Port | Responsibility |
|---|---|---|
| gateway-service | 8000 | Single entry point, JWT auth, rate limiting, routing |
| rag-service | 8001 | Document ingestion, chunking, embedding, vector search |
| llm-service | 8002 | LLM inference, RAG-powered answer generation |
| memory-service | 8003 | Conversation history, session state, agent handoff |
| agent-service | 8004 | Multi-agent orchestration, task decomposition, LangGraph |

## Domain Agent Services

| Service | Port | External API | Capability | Status |
|---|---|---|---|---|
| weather-agent | 8011 | OpenWeatherMap | Current weather, 5-day forecast | ✅ Live |
| search-agent | 8012 | DuckDuckGo | Real-time web + news search | ✅ Live |
| travel-agent | 8010 | Amadeus / Skyscanner | Flights, hotels, trains | Planned |
| finance-agent | 8013 | Alpha Vantage / CoinGecko | Stocks, currency, crypto | Planned |
| news-agent | 8014 | NewsAPI | Latest news by topic | Planned |
| calendar-agent | 8015 | Google Calendar | Schedules, reminders | Planned |
| maps-agent | 8016 | Google Maps | Directions, nearby places | Planned |
| email-agent | 8017 | Gmail API | Send, read, summarize emails | Planned |

## Infrastructure & Observability

| Service | Port | Responsibility |
|---|---|---|
| qdrant | 6333 | Vector database |
| ollama | 11434 | Local LLM runtime (llama3.2:3b, CPU inference) |
| postgres-gateway | 5432 | Users, refresh tokens |
| postgres-memory | 5432 | Sessions, message history |
| redis-gateway | 6379 | Rate limiting |
| redis-memory | 6379 | Session cache |
| redis-weather | 6379 | Weather response cache |
| redis-search | 6379 | Search response cache |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Metrics dashboards |
| blackbox-exporter | 9115 | External endpoint probing |
| node-exporter | 9100 | Per-node hardware metrics (DaemonSet) |
| fluent-bit | 2020 | Cluster-wide log collection (DaemonSet) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| LLM Runtime | Ollama (llama3.2:3b), CPU inference |
| Agent Orchestration | LangGraph |
| Vector Database | Qdrant |
| Embeddings | FastEmbed (BAAI/bge-small-en-v1.5, CPU) |
| Relational DB | PostgreSQL + SQLAlchemy (async) + Alembic |
| Cache | Redis |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v2 |
| Logging | Structlog |
| Observability | Prometheus, Grafana, node-exporter, fluent-bit, blackbox-exporter |
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes (k3s) |

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- k3s (optional, for Kubernetes deployment)

### Run with Docker Compose

```bash
git clone https://github.com/yourusername/agentica.git
cd agentica

docker compose up --build

# pull the LLM model (first time only)
docker exec -it agentica-ollama ollama pull llama3.2:3b
```

### Run a service locally (development)

```bash
cd services/core/rag-service

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

docker run -d -p 6333:6333 qdrant/qdrant

uvicorn app.main:app --reload --port 8001
```

### Deploy to Kubernetes (k3s)

```bash
kubectl apply -f infra/k8s/namespace.yml
kubectl apply -f infra/k8s/config/
kubectl apply -f infra/k8s/storage/
kubectl apply -f infra/k8s/infrastructure/
kubectl apply -f infra/k8s/daemonsets/
kubectl apply -f infra/k8s/services/
kubectl apply -f infra/k8s/ingress/

kubectl get pods -n agentica
```

---

## API Endpoints

### Gateway Service (port 8000)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Authenticate and get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user profile |
| POST | `/api/v1/proxy/{service}/{path}` | Authenticated proxy to upstream services |
| GET | `/health` | Health check including upstream status |

### RAG Service (port 8001)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ingest` | Ingest raw text into vector DB |
| POST | `/api/v1/ingest/file` | Ingest .pdf or .txt file |
| POST | `/api/v1/search` | Semantic similarity search |
| POST | `/api/v1/query` | RAG query — retrieves context + calls llm-service for answer |
| GET | `/health` | Health check |

### LLM Service (port 8002)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/complete` | Single prompt completion |
| POST | `/api/v1/chat` | Multi-turn conversation |
| POST | `/api/v1/chat/rag` | RAG-powered chat with context chunks |
| GET | `/health` | Health check including Ollama status |

### Memory Service (port 8003)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sessions` | Create a conversation session |
| GET | `/api/v1/sessions/{id}` | Get session by ID |
| GET | `/api/v1/sessions/user/{user_id}` | Get all sessions for a user |
| POST | `/api/v1/sessions/messages` | Save a message to a session |
| POST | `/api/v1/sessions/history` | Get conversation history (Redis-cached) |
| DELETE | `/api/v1/sessions/{id}` | Delete a session |
| DELETE | `/api/v1/sessions/{id}/history` | Clear session history |

### Weather Agent (port 8011)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/weather/current` | Current weather for a city |
| POST | `/api/v1/weather/forecast` | 5-day forecast |
| POST | `/api/v1/weather/summary` | Natural language summary for agent-service |

### Search Agent (port 8012)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/search/web` | Web search |
| POST | `/api/v1/search/news` | News search |
| POST | `/api/v1/search/summary` | Natural language summary for agent-service |

### Interactive API Docs

Each service exposes Swagger UI at `/docs`, e.g. `http://localhost:8001/docs`.

---

## How It Works

### RAG Pipeline

```
Document
    → chunking (512 tokens, 50 overlap)
    → embedding (BAAI/bge-small-en-v1.5, 384 dimensions, CPU)
    → storage (Qdrant vector DB)

Query
    → embed question
    → cosine similarity search (Qdrant)
    → retrieve top-k chunks
    → POST to llm-service /chat/rag with question + chunks
    → return grounded answer
```

### Service Communication

```
rag-service → llm-service       : HTTP REST (gRPC planned)
gateway-service → all services  : HTTP REST proxy, JWT-authenticated
Session state                   : Redis (per-service isolated DBs)
Persistent state                : PostgreSQL (per-service isolated databases)
```

---

## Running Tests

```bash
cd services/core/rag-service
pytest tests/ -v

cd services/core/llm-service
pytest tests/ -v

cd services/core/memory-service
pytest tests/ -v
```

All test suites use `pytest-asyncio`, mocked upstream clients, and `conftest.py` shared fixtures.

---

## Environment Variables

### RAG Service

| Variable | Default | Description |
|---|---|---|
| `QDRANT_HOST` | localhost | Qdrant host |
| `QDRANT_COLLECTION` | agentica | Collection name |
| `EMBEDDING_MODEL` | BAAI/bge-small-en-v1.5 | Embedding model |
| `CHUNK_SIZE` | 512 | Chunk size in tokens |
| `LLM_SERVICE_URL` | http://localhost:8002 | LLM service URL |

### LLM Service

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | localhost | Ollama host |
| `OLLAMA_MODEL` | llama3.2:3b | Model name |
| `TEMPERATURE` | 0.7 | Generation temperature |
| `MAX_TOKENS` | 1024 | Max tokens per response |

---

## Kubernetes Deployment Status

Deployed and verified on a local single-node **k3s** cluster:

| Component | Type | Status |
|---|---|---|
| gateway-service | Deployment | ✅ Running |
| agent-service | Deployment | ✅ Running |
| rag-service | Deployment | ✅ Running |
| llm-service | Deployment | ✅ Running |
| memory-service | Deployment | ✅ Running |
| search-agent | Deployment | ✅ Running |
| weather-agent | Deployment | ✅ Running |
| ollama | StatefulSet | ✅ Running |
| qdrant | StatefulSet | ✅ Running |
| postgres-gateway | StatefulSet | ✅ Running |
| postgres-memory | StatefulSet | ✅ Running |
| redis-gateway | StatefulSet | ✅ Running |
| redis-memory | StatefulSet | ✅ Running |
| redis-search | StatefulSet | ✅ Running |
| redis-weather | StatefulSet | ✅ Running |
| prometheus | StatefulSet | ✅ Running |
| grafana | Deployment | ✅ Running |
| blackbox-exporter | Deployment | ✅ Running |
| node-exporter | DaemonSet | ✅ Running |
| fluent-bit | DaemonSet | ✅ Running |

> **20/20 workloads healthy on Kubernetes (k3s).**

---

## Roadmap

### Phase 1 — Core Platform ✅
- [x] RAG Service
- [x] LLM Service
- [x] Memory Service
- [x] Agent Service (LangGraph)
- [x] Gateway Service (JWT auth, rate limiting, proxy)
- [x] Docker Compose

### Phase 2 — Domain Agents (in progress)
- [x] Weather Agent
- [x] Search Agent
- [ ] Travel Agent
- [ ] Finance Agent
- [ ] News Agent
- [ ] Calendar Agent
- [ ] Maps Agent
- [ ] Email Agent

### Phase 3 — Production Hardening (in progress)
- [x] Kubernetes manifests (k3s)
- [x] Prometheus + Grafana observability
- [x] DaemonSets — node-exporter, fluent-bit
- [ ] gRPC inter-service communication
- [ ] CI/CD (GitHub Actions)
- [ ] OAuth2 social login

---

## Contributing

Pull requests are welcome. For major changes please open an issue first.

---

## License

MIT
```