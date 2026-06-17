'''Main'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.utils.logger import setup_logging, get_logger
# from app.db.base import init_db
from app.core.cache import redis_cache
from app.api.v1.routers import register_routers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize database and cache on startup."""
    # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("llm_service_starting", env=settings.APP_ENV)

    # init postgres tables
    # await init_db()
    # logger.info("db_initialized")

    # check redis
    redis_ok = await redis_cache.health()
    if not redis_ok:
        logger.warning("redis_not_reachable", host=settings.REDIS_HOST)
    else:
        logger.info("redis_connected")

    yield
    logger.info("memory_service_stopping")


app = FastAPI(
    title="Agentica Memory Service",
    description="Conversation session and message history management service",
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

register_routers(app)


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    redis_ok = await redis_cache.health()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "redis": "connected" if redis_ok else "unreachable",
    }
