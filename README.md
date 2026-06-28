# Agentica

A production-grade agentic AI orchestration platform built with FastAPI, Ollama, and Qdrant.
Agentica enables natural language interaction with real-world services — users can plan trips,
check weather, search the web, manage schedules, and more through a unified AI agent layer.

> Built as a professional portfolio project demonstrating real-world AI engineering,
> microservices architecture, and agentic AI orchestration skills.

---

## Vision

A single user message like:

"Plan me a 3-day trip to Paris next weekend, find the cheapest flights from Tehran,
book a hotel near the Eiffel Tower under $100/night,
and tell me what to pack based on the weather forecast."

Gets automatically orchestrated across multiple specialized agents:

gateway-service (auth + routing)
→ agent-service (orchestrator)
→ travel-agent  (flights + hotels)
→ weather-agent (Paris forecast)
→ llm-service   (packing suggestions)
→ memory-service (save trip plan)
→ return complete plan to user

---

## Architecture
agentica/
├── services/
│   ├── rag-service/           # Document ingestion, embedding, retrieval        (port 8001)
│   ├── llm-service/           # LLM inference, RAG-powered chat                 (port 8002)
│   ├── memory-service/        # Conversation history, session management        (port 8003)
│   ├── agent-service/         # Agent orchestration, multi-step reasoning       (port 8004)
│   ├── gateway-service/       # Auth, routing, rate limiting                    (port 8000)
│   ├── travel-agent/          # Flights, hotels, trains                         (port 8010)
│   ├── weather-agent/         # Weather forecasts                               (port 8011)
│   ├── search-agent/          # Web search, real-time information               (port 8012)
│   ├── finance-agent/         # Stocks, currency, crypto                        (port 8013)
│   ├── news-agent/            # Latest news                                     (port 8014)
│   ├── calendar-agent/        # Schedule management, reminders                  (port 8015)
│   ├── maps-agent/            # Directions, nearby places                       (port 8016)
│   └── email-agent/           # Send/read emails                                (port 8017)
├── infra/
│   └── k8s/                   # Kubernetes manifests (k3s)
├── docker-compose.yml
└── README.md

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

| Service | Port | External API | Capability |
|---|---|---|---|
| travel-agent | 8010 | Amadeus / Skyscanner | Flights, hotels, trains |
| weather-agent | 8011 | OpenWeatherMap | Forecasts, alerts |
| search-agent | 8012 | SerpAPI / Brave Search | Real-time web search |
| finance-agent | 8013 | Alpha Vantage / CoinGecko | Stocks, currency, crypto |
| news-agent | 8014 | NewsAPI | Latest news by topic |
| calendar-agent | 8015 | Google Calendar | Schedules, reminders |
| maps-agent | 8016 | Google Maps | Directions, nearby places |
| email-agent | 8017 | Gmail API | Send, read, summarize emails |

## Infrastructure Services

| Service | Port | Responsibility |
|---|---|---|
| qdrant | 6333 | Vector database |
| ollama | 11434 | Local LLM runtime (llama3.2:3b) |
| redis | 6379 | Session cache, short-term memory |
| rabbitmq | 5672 | Async task queues between agents |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Metrics visualization |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| LLM Runtime | Ollama (llama3.2:3b) |
| Agent Orchestration | LangGraph |
| Vector Database | Qdrant |
| Embeddings | FastEmbed (BAAI/bge-small-en-v1.5) |
| Validation | Pydantic v2 |
| Logging | Structlog |
| Message Queue | RabbitMQ |
| Cache | Redis |
| Observability | Prometheus + Grafana |
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes (k3s) |

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.11+

### Run with Docker Compose

```bash
# clone the repository
git clone https://github.com/yourusername/agentica.git
cd agentica

# start all services
docker compose up --build

# pull the LLM model (first time only)
docker exec -it agentica-ollama ollama pull llama3.2:3b
```

### Run a service locally (development)

```bash
cd services/rag-service

# create virtual environment
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# start qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# run the service
uvicorn app.main:app --reload --port 8001
```

---

## API Endpoints

### Gateway Service (port 8000)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate and get JWT token |
| POST | `/auth/register` | Register new user |
| POST | `/agent/chat` | Main entry point — send message to agent orchestrator |
| GET | `/health` | Health check |

### RAG Service (port 8001)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ingest` | Ingest raw text into vector DB |
| POST | `/api/v1/ingest/file` | Ingest .pdf or .txt file |
| POST | `/api/v1/search` | Semantic similarity search |
| POST | `/api/v1/query` | RAG query — retrieves context + generates answer |
| GET | `/health` | Health check |

### LLM Service (port 8002)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/complete` | Single prompt completion |
| POST | `/api/v1/chat` | Multi-turn conversation |
| POST | `/api/v1/chat/rag` | RAG-powered chat with context chunks |
| GET | `/health` | Health check |

### Agent Service (port 8004)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/agent/run` | Run a multi-step agent task |
| POST | `/api/v1/agent/chat` | Conversational agent with tool use |
| GET | `/api/v1/agent/tasks/{task_id}` | Get task status and result |
| GET | `/health` | Health check |

### Interactive API Docs

Each service exposes Swagger UI at `/docs`:
- Gateway: http://localhost:8000/docs
- RAG Service: http://localhost:8001/docs
- LLM Service: http://localhost:8002/docs
- Agent Service: http://localhost:8004/docs

---

## How It Works

### RAG Pipeline
Document
→ chunking (512 tokens, 50 overlap)
→ embedding (BAAI/bge-small-en-v1.5, 384 dimensions)
→ storage (Qdrant vector DB)
Query
→ embed question
→ cosine similarity search (Qdrant)
→ retrieve top-k chunks
→ send question + chunks to LLM
→ return grounded answer

### Agentic Pipeline
User message
→ gateway-service (auth + routing)
→ agent-service (task decomposition via LangGraph)
→ parallel tool calls to domain agents
→ results aggregated
→ llm-service generates final response
→ memory-service stores conversation
→ return to user

### Service Communication
Internal services  → HTTP/REST (current) → gRPC (planned)
External clients   → REST API via gateway-service
Async tasks        → RabbitMQ message queues
Session state      → Redis

---

## Running Tests

```bash
# rag-service
cd services/rag-service
pip install pytest pytest-asyncio httpx
pytest tests/ -v

# llm-service
cd services/llm-service
pytest tests/ -v
```

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

The following services are currently deployed and running on a local **k3s** cluster.

| Component | Type | Status | Replicas |
|-----------|------|--------|----------|
| gateway-service | Deployment | ✅ Running | 1/1 |
| agent-service | Deployment | ✅ Running | 1/1 |
| rag-service | Deployment | ✅ Running | 1/1 |
| llm-service | Deployment | ✅ Running | 1/1 |
| memory-service | Deployment | ✅ Running | 1/1 |
| search-service | Deployment | ✅ Running | 1/1 |
| weather-service | Deployment | ✅ Running | 1/1 |
| ollama | StatefulSet | ✅ Running | 1/1 |
| qdrant | StatefulSet | ✅ Running | 1/1 |
| postgres-gateway | StatefulSet | ✅ Running | 1/1 |
| postgres-memory | StatefulSet | ✅ Running | 1/1 |
| redis-gateway | StatefulSet | ✅ Running | 1/1 |
| redis-memory | StatefulSet | ✅ Running | 1/1 |
| redis-search | StatefulSet | ✅ Running | 1/1 |
| redis-weather | StatefulSet | ✅ Running | 1/1 |
| prometheus | StatefulSet | ✅ Running | 1/1 |
| grafana | Deployment | ✅ Running | 1/1 |
| blackbox-exporter | Deployment | ✅ Running | 1/1 |

> **Current cluster status:** 18/18 workloads are healthy and running on Kubernetes (k3s).

## Roadmap

### Phase 1 — Core Platform
- [x] RAG Service
- [x] LLM Service
- [x] Docker Compose
- [x] Memory Service
- [x] Agent Service (LangGraph)
- [x] Gateway Service

### Phase 2 — Domain Agents
- [x] Weather Agent
- [x] Search Agent
- [ ] Travel Agent
- [ ] Finance Agent
- [ ] News Agent

### Phase 3 — Production
- [ ] Auth Service (JWT + OAuth2)
- [x] Kubernetes manifests (k3s)
- [x] Prometheus + Grafana observability
- [ ] gRPC inter-service communication
- [ ] Calendar Agent
- [ ] Maps Agent
- [ ] Email Agent

---

## Contributing

Pull requests are welcome. For major changes please open an issue first.

---

## License

MIT
