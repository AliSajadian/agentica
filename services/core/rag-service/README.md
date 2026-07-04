# RAG Service

A production-ready Retrieval-Augmented Generation (RAG) service built with FastAPI, Qdrant, and FastEmbed. This service provides document ingestion, semantic search, and intelligent querying capabilities.

## 🚀 Features

- **Document Ingestion**: Upload and process text, PDF, and TXT files
- **Semantic Search**: Vector similarity search using BAAI/bge-small-en-v1.5 embeddings
- **Intelligent Querying**: RAG-powered question answering with LLM integration
- **Local Embeddings**: No external API calls for embeddings - runs locally
- **RESTful API**: Clean, well-documented API endpoints
- **Validation**: Pydantic-based request validation

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Technical Details](#technical-details)
- [Testing](#testing)
- [Configuration](#configuration)

## 🏃 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Check health
curl http://localhost:8001/health
```

## 🔧 API Endpoints

### Health Check

```bash
curl http://localhost:8001/health
```

### Document Ingestion (`/api/v1/ingest`)

Ingest text documents with optional metadata.

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern Python web framework for building APIs fast.",
    "source": "test.txt",
    "metadata": {
      "author": "FastAPI Team",
      "category": "Framework",
      "language": "English"
    }
  }'
```

**Response:**
```json
{
  "document_id": "a5c04ec4-...",
  "chunks": 1,
  "status": "success"
}
```

### File Upload Ingestion (`/api/v1/query/file`)

Upload PDF or TXT files for ingestion.

```bash
curl -X POST http://localhost:8001/api/v1/query/file \
  -F "file=@document.pdf"
```

### Semantic Search (`/api/v1/search`)

Pure vector similarity search - returns relevant chunks without LLM generation.

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what is FastAPI?",
    "top_k": 3,
    "score_threshold": 0.3,
    "metadata_filter": null
  }'
```

**Response:**
```json
{
  "results": [
    {
      "text": "FastAPI is a modern Python web framework...",
      "metadata": {"source": "test.txt", "score": 0.85},
      "id": "uuid-here"
    }
  ]
}
```

### Intelligent Query (`/api/v1/query`)

RAG-powered question answering - retrieves relevant chunks AND generates an answer using LLM.

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "what is LangGraph used for?",
    "top_k": 3,
    "score_threshold": 0.3,
    "metadata_filter": null
  }'
```

## 🏗️ Architecture

The service follows a clean, modular architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐    ┌─────────────────┐  │
│  │   /ingest    │  │   /search    │    │   /query        │  │
│  └──────┬───────┘  └──────┬───────┘    └────────┬────────┘  │
│         │                 │                     │           │
│         └─────────────────┼─────────────────────┘           │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │                    Services Layer                     │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │   Text      │  │  Embedding  │  │   Qdrant    │    │  │
│  │  │  Chunker    │  │   Service   │  │   Service   │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │   External Services   │
                ├───────────────────────┤
                │  ┌─────────────────┐  │
                │  │   Qdrant DB     │  │
                │  │  (Vector Store) │  │
                │  └─────────────────┘  │
                │  ┌─────────────────┐  │
                │  │  LLM Service    │  │
                │  │  (Optional)     │  │
                │  └─────────────────┘  │
                └───────────────────────┘
```

### Component Descriptions

#### 1. **FastAPI Application**
- Handles HTTP requests and responses
- Pydantic schema validation for all requests
- Route definitions and error handling

#### 2. **Services Layer**

- **Text Chunker**: Splits documents into manageable chunks
  - Configurable `CHUNK_SIZE` (default: 512)
  - Intelligent splitting preserving semantic boundaries

- **Embedding Service**: Generates vector embeddings
  - Uses `BAAI/bge-small-en-v1.5` model
  - Runs locally on CPU (no external API calls)
  - Outputs 384-dimensional vectors

- **Qdrant Service**: Vector database operations
  - Stores document chunks with their embeddings
  - Performs cosine similarity searches
  - Metadata filtering capabilities

#### 3. **Data Flow**

**Ingestion Flow:**
1. Request received and validated via Pydantic
2. Text split into chunks (if needed)
3. Each chunk embedded using FastEmbed
4. Vectors stored in Qdrant with metadata

**Search Flow:**
1. Query text received and validated
2. Query converted to embedding using same model
3. Qdrant performs cosine similarity search
4. Returns top-k results above threshold

## 🔬 Technical Details

### Embedding Model
- **Model**: BAAI/bge-small-en-v1.5
- **Dimensions**: 384
- **Runtime**: Local CPU (no external API)
- **Performance**: Optimized for semantic similarity

### Vector Database (Qdrant)
- **Collection**: `agentica`
- **Distance Metric**: Cosine similarity
- **Indexing**: HNSW for efficient retrieval
- **Persistence**: Local file-based storage

### Chunking Strategy
- **Default Size**: 512 characters
- **Overlap**: Configurable
- **Method**: Semantic boundary detection

### File Processing
- **PDF**: Extracts text using PyPDF2
- **TXT**: Direct text extraction
- **Metadata**: Auto-populates source filename

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

### Test Coverage

```bash
pytest tests/ --cov=app --cov-report=term
```

## ⚙️ Configuration

Create a `.env` file:

```env
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=agentica

# Embedding Configuration
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=512

# LLM Configuration (optional)
LLM_API_URL=http://localhost:8002/api/v1/generate
```

## 📊 Performance Considerations

- **Embedding Generation**: ~50ms per 512-character chunk on CPU
- **Search Latency**: ~10-50ms for top-k retrieval
- **Concurrency**: FastAPI supports async operations
- **Memory**: Model uses ~500MB RAM

## 🎯 Use Cases

1. **Document QA**: Ask questions about uploaded documents
2. **Semantic Search**: Find relevant content by meaning, not just keywords
3. **Knowledge Base**: Build searchable company documentation
4. **Chatbots**: Power conversational AI with retrieved context

## 🔮 Roadmap

- [x] Support for more file formats (DOCX, HTML, MD)
- [x] Hybrid search (semantic + keyword)
- [x] Batch ingestion endpoints
- [x] WebSocket streaming for queries
- [x] Kubernetes deployment manifests
- [x] Prometheus metrics
- [x] OpenTelemetry integration

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


MIT License