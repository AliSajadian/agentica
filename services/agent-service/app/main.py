'''Main'''
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.api.v1.routes import agents as agent_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Application lifespan: setup and teardown."""
        # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("agent_service_startup", env=settings.APP_ENV, port=settings.APP_PORT)

    yield
    logger.info("agent_service_shutdown")


app = FastAPI(
    title="agent-service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(agent_router.router, prefix="/api/v1/agent", tags=["agent"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "agent-service"}
