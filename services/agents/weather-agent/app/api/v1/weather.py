from fastapi import APIRouter, HTTPException
from app.services.weather import weather_service
from app.models.schemas import (
    WeatherRequest, WeatherResponse,
    ForecastRequest, ForecastResponse,
    WeatherSummaryRequest, WeatherSummaryResponse
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/current", response_model=WeatherResponse)
async def get_current_weather(request: WeatherRequest):
    """
    Get current weather for a city.
    Returns temperature, humidity, wind, and conditions.
    """
    try:
        logger.info("current_weather_started", city=request.city)
        return await weather_service.get_current(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("current_weather_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest):
    """
    Get weather forecast for up to 5 days.
    Returns 3-hour interval data points with rain probability.
    """
    try:
        logger.info("forecast_started", city=request.city, days=request.days)
        return await weather_service.get_forecast(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("forecast_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=WeatherSummaryResponse)
async def get_weather_summary(request: WeatherSummaryRequest):
    """
    Get natural language weather summary for agent-service.
    Combines current weather and optional forecast into a human-readable string.
    """
    try:
        logger.info("summary_started", city=request.city)
        return await weather_service.get_summary(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
