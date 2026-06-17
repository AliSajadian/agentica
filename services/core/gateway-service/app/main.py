'''Main'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.db.base import init_db
from app.core.rate_limiter import rate_limiter
from app.services.proxy import proxy_service
from app.api.v1 import auth, proxy

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Initialize database, cache and upstream health on startup."""
    # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("gateway_service_starting", env=settings.APP_ENV)

    await init_db()
    logger.info("db_initialized")

    redis_ok = await rate_limiter.health()
    if not redis_ok:
        logger.warning("redis_not_reachable", host=settings.REDIS_HOST)
    else:
        logger.info("redis_connected")

    upstream = await proxy_service.health_check_all()
    logger.info("upstream_health", **upstream)

    yield
    logger.info("gateway_service_stopping")


app = FastAPI(
    title="Agentica Gateway Service",
    description="Single entry point — auth, rate limiting, and request routing",
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

app.include_router(auth.router,  prefix="/api/v1/auth",  tags=["auth"])
app.include_router(proxy.router, prefix="/api/v1/proxy", tags=["proxy"])


@app.get("/health", tags=["health"])
async def health():
    """Health check including upstream service status."""
    redis_ok = await rate_limiter.health()
    upstream = await proxy_service.health_check_all()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "redis": "connected" if redis_ok else "unreachable",
        "upstream": upstream
    }
