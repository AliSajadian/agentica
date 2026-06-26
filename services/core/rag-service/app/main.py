'''Main'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import ingest, search, query
from app.config import settings
from app.core.embeddings import embedding_service
from app.services.qdrant import qdrant_service
from app.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    '''Life span'''
    # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("rag_service_starting", env=settings.APP_ENV)
    
    # init qdrant collection
    from app.services.qdrant import qdrant_service
    await qdrant_service.init_collection(vector_size=384)
    
    # Warmup embedding model (lazy loading triggered once during startup)
    try:
        from app.core.embeddings import embedding_service
        embedding_service.embed_single("warmup")
        logger.info("embedding_model_warmup_complete")
    except Exception as e:
        logger.warning("embedding_model_warmup_failed", error=str(e))
        # Don't fail startup if embedding warmup fails - it will load on first request

    yield
    # shutdown
    logger.info("rag_service_stopping")

app = FastAPI(
    title="Agentica RAG Service",
    description="Document ingestion, embedding and retrieval service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://agentica.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(query.router,  prefix="/api/v1", tags=["query"])


@app.get("/health", tags=["health"])
async def health():
    '''Health'''
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/ready", tags=["health"])
async def ready():
    """Readiness check including Qdrant connectivity."""
    try:
        # Check Qdrant connection
        await qdrant_service.client.get_collections()
                
        return {
            "status": "ok",
            "service": "rag-service",
            "env": settings.APP_ENV,
            "qdrant": "connected",
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "rag-service",
                "error": str(e)
            }
        )

