import json
import redis.asyncio as aioredis
from app.core.openweather import openweather_client
from app.models.schemas import (
    WeatherResponse, WeatherRequest,
    ForecastResponse, ForecastRequest,
    ForecastItem, WeatherSummaryRequest,
    WeatherSummaryResponse
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_PREFIX_CURRENT = "weather:current:"
CACHE_PREFIX_FORECAST = "weather:forecast:"


class WeatherService:
    """Orchestrates weather data fetching, caching and formatting."""

    def __init__(self):
        """Initialize Redis cache client."""
        self.cache = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.ttl = settings.WEATHER_CACHE_TTL

    async def get_current(self, request: WeatherRequest) -> WeatherResponse:
        """
        Get current weather for a city.
        Returns cached result if available, otherwise fetches from API.
        """
        cache_key = f"{CACHE_PREFIX_CURRENT}{request.city}:{request.country_code}:{request.units}"

        # check cache
        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return WeatherResponse(**cached)

        # fetch from API
        data = await openweather_client.get_current(
            city=request.city,
            country_code=request.country_code,
            units=request.units.value
        )

        result = self._parse_current(data, request.units)

        # cache result
        await self._set_cache(cache_key, result.model_dump())
        logger.info("weather_current_fetched", city=request.city)
        return result

    async def get_forecast(self, request: ForecastRequest) -> ForecastResponse:
        """
        Get weather forecast for a city.
        Returns cached result if available, otherwise fetches from API.
        """
        cache_key = f"{CACHE_PREFIX_FORECAST}{request.city}:{request.country_code}:{request.units}"

        # check cache
        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return ForecastResponse(**cached)

        # fetch from API
        data = await openweather_client.get_forecast(
            city=request.city,
            country_code=request.country_code,
            units=request.units.value
        )

        result = self._parse_forecast(data, request.days, request.units)

        # cache result
        await self._set_cache(cache_key, result.model_dump())
        logger.info("weather_forecast_fetched", city=request.city)
        return result

    async def get_summary(self, request: WeatherSummaryRequest) -> WeatherSummaryResponse:
        """
        Get natural language weather summary for agent-service consumption.
        Combines current weather and optionally forecast into a human-readable string.
        """
        current = await self.get_current(WeatherRequest(
            city=request.city,
            country_code=request.country_code,
            units=request.units.value
        ))

        forecast = None
        if request.include_forecast:
            forecast = await self.get_forecast(ForecastRequest(
                city=request.city,
                country_code=request.country_code,
                units=request.units.value
            ))

        unit_symbol = "°C" if request.units == "metric" else "°F"
        summary = (
            f"Current weather in {current.city}, {current.country}: "
            f"{current.description.capitalize()}, "
            f"temperature {current.temperature}{unit_symbol} "
            f"(feels like {current.feels_like}{unit_symbol}), "
            f"humidity {current.humidity}%, "
            f"wind speed {current.wind_speed} {'m/s' if request.units == 'metric' else 'mph'}."
        )

        if forecast:
            summary += f" 5-day forecast available with {len(forecast.forecast)} data points."

        logger.info("weather_summary_built", city=request.city)
        return WeatherSummaryResponse(
            city=current.city,
            summary=summary,
            current=current,
            forecast=forecast
        )

    def _parse_current(self, data: dict, units: str) -> WeatherResponse:
        """Parse raw OpenWeatherMap current weather response into WeatherResponse."""
        wind = data.get("wind", {})
        return WeatherResponse(
            city=data["name"],
            country=data["sys"]["country"],
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            temp_min=data["main"]["temp_min"],
            temp_max=data["main"]["temp_max"],
            humidity=data["main"]["humidity"],
            pressure=data["main"]["pressure"],
            description=data["weather"][0]["description"],
            icon=data["weather"][0]["icon"],
            wind_speed=wind.get("speed", 0),
            wind_direction=wind.get("deg"),
            visibility=data.get("visibility"),
            units=units,
            cached=False
        )

    def _parse_forecast(self, data: dict, days: int, units: str) -> ForecastResponse:
        """Parse raw OpenWeatherMap forecast response into ForecastResponse."""
        items = []
        # API returns 3-hour intervals — take first 8 per day (8 * 3h = 24h)
        slots = data["list"][:days * 8]

        for slot in slots:
            items.append(ForecastItem(
                datetime=slot["dt_txt"],
                temperature=slot["main"]["temp"],
                feels_like=slot["main"]["feels_like"],
                description=slot["weather"][0]["description"],
                icon=slot["weather"][0]["icon"],
                humidity=slot["main"]["humidity"],
                wind_speed=slot["wind"]["speed"],
                rain_probability=slot.get("pop", 0.0)
            ))

        return ForecastResponse(
            city=data["city"]["name"],
            country=data["city"]["country"],
            days=days,
            forecast=items,
            units=units,
            cached=False
        )

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve cached weather data from Redis."""
        try:
            value = await self.cache.get(key)
            if value:
                logger.info("weather_cache_hit", key=key)
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("weather_cache_get_failed", error=str(e))
            return None

    async def _set_cache(self, key: str, value: dict):
        """Store weather data in Redis with TTL."""
        try:
            await self.cache.setex(key, self.ttl, json.dumps(value))
        except Exception as e:
            logger.error("weather_cache_set_failed", error=str(e))


weather_service = WeatherService()
