# pylint: disable=import-outside-toplevel
'''
Main
'''
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.core.openflights import openflights_data
from app.api.v1.routers import register_routers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Application lifespan: setup and teardown."""
        # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("travel_agent_starting", env=settings.APP_ENV)

    # load static datasets into memory
    openflights_data.load()

    logger.info(
        "datasets_loaded",
        airports=len(openflights_data.airports),
        routes=len(openflights_data.routes),
        airlines=len(openflights_data.airlines)
    )

    yield
    logger.info("travel_agent_stopping")


app = FastAPI(
    title="Agentica Travel Agent",
    description=(
        "Flight routes, airport and airline data via OpenFlights static dataset. "
        "Swap core/openflights.py for Amadeus or Aviationstack when live API access is available."
    ),
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

register_routers(app)

@app.get("/health", tags=["health"])
async def health():
    """Health check including dataset load status."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "data_loaded": openflights_data.is_loaded(),
        "airports": len(openflights_data.airports) if openflights_data.is_loaded() else 0,
        "routes": len(openflights_data.routes) if openflights_data.is_loaded() else 0,
        "airlines": len(openflights_data.airlines) if openflights_data.is_loaded() else 0,
    }


@app.get("/ready", tags=["health"])
async def ready():
    """Readiness probe — returns 200 only when datasets are fully loaded."""
    if not openflights_data.is_loaded():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Datasets not loaded yet")
    return {"status": "ready"}
