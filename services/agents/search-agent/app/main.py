from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.tavily import search_client

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.api.v1 import search

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(appFastAPI: FastAPI):
    """Check search API reachability on startup."""
    setup_logging()
    
    logger.info(f"starting {appFastAPI.title}...")
    logger.info("search_agent_starting", env=settings.APP_ENV)

    api_ok = await search_client.health()
    if not api_ok:
        logger.warning("search_api_unreachable")
    else:
        logger.info("search_api_connected")

    yield
    logger.info("search_agent_stopping")


app = FastAPI(
    title="Agentica Search Agent",
    description="Real-time web and news search via DuckDuckGo",
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

app.include_router(search.router, prefix="/api/v1/search", tags=["search"])


@app.get("/health", tags=["health"])
async def health():
    """Health check including search API status."""
    api_ok = await search_client.health()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "search_api": "connected" if api_ok else "unreachable",
        "provider": settings.SEARCH_PROVIDER
    }
