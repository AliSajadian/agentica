from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.core.openweather import openweather_client
from app.api.v1 import weather
from app.services.weather import weather_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Check OpenWeatherMap API reachability on startup."""
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("weather_agent_starting", env=settings.APP_ENV)

    api_ok = await openweather_client.health()
    if not api_ok:
        logger.warning("openweather_api_unreachable")
    else:
        logger.info("openweather_api_connected")

    yield
    logger.info("weather_agent_stopping")


app = FastAPI(
    title="Agentica Weather Agent",
    description="Real-time weather data and forecasts via OpenWeatherMap",
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

app.include_router(weather.router, prefix="/api/v1/weather", tags=["weather"])


@app.get("/health", tags=["health"])
async def health():
    """Health check including OpenWeatherMap API status."""
    # api_ok = await openweather_client.health()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        # "openweather_api": "connected" if api_ok else "unreachable",
    }


@app.get("/ready")
async def ready():
    """Check if Redis is reachable."""
    try:
        # Check OpenWeather connectivity
        api_ok = await openweather_client.health()

        # Check Redis connectivity
        redis_ok = await weather_service._get_client().ping()
                
        # Check if all critical services are ready
        all_ready = api_ok and redis_ok
        
        status_code = 200 if all_ready else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_ready else "not_ready",
                "service": settings.APP_NAME,
                "env": settings.APP_ENV,
                "openweather": "connected" if api_ok else "unreachable",
                "redis": "connected" if redis_ok else "unreachable"
            }
        )
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.APP_NAME,
                "error": str(e)
            }
        )
