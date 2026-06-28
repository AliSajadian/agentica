'''Main'''
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

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

Instrumentator().instrument(app).expose(app)

app.include_router(agent_router.router, prefix="/api/v1/agent", tags=["agent"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "agent-service"}


import httpx
from app.config import settings

@app.get("/ready")
async def ready():
    """Check if all dependent services are reachable."""
    errors = []
    
    # Check RAG service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.RAG_SERVICE_URL}/health")
            if resp.status_code != 200:
                errors.append("rag_service_unhealthy")
    except Exception:
        errors.append("rag_service_unreachable")
    
    # Check LLM service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.LLM_SERVICE_URL}/health")
            if resp.status_code != 200:
                errors.append("llm_service_unhealthy")
    except Exception:
        errors.append("llm_service_unreachable")
    
    # Check Memory service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/health")
            if resp.status_code != 200:
                errors.append("memory_service_unhealthy")
    except Exception:
        errors.append("memory_service_unreachable")
    
    if errors:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "agent-service",
                "errors": errors
            }
        )
    
    return {
        "status": "ok",
        "service": "agent-service",
        "dependencies": {
            "rag": "connected",
            "llm": "connected",
            "memory": "connected"
        }
    }
