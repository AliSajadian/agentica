'''Main'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.api.v1 import ingest, search, query

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    ''''Life span'''
    # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("rag_service_starting", env=settings.APP_ENV)
    # init qdrant collection
    from app.services.qdrant import qdrant_service
    await qdrant_service.init_collection(vector_size=384)

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
