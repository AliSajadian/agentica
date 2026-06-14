import httpx
from app.config import settings
from app.utils.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger(__name__)


class OpenWeatherClient:
    """HTTP client for OpenWeatherMap API."""

    def __init__(self):
        """Initialize client with API key and base URL."""
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.timeout = 30

    async def get_current(self, city: str, country_code: str = None, units: str = "metric") -> dict:
        """
        Fetch current weather for a city from OpenWeatherMap API.
        Raises 404 if city not found, 401 if API key invalid.
        """
        query = f"{city},{country_code}" if country_code else city
        params = {
            "q": query,
            "appid": self.api_key,
            "units": str(units.value) if hasattr(units, 'value') else units,
            "lang": settings.OPENWEATHER_LANG
        }
        logger.info("openweather_params", params=params)
        logger.info("openweather_current_request", city=city, units=units)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("***current openweather_request_debug", 
                    url=f"{self.base_url}/weather",
                    params=params,
                    units_value=units
                )

                response = await client.get(
                    f"{self.base_url}/weather",
                    params=params
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"City '{city}' not found"
                    )
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid OpenWeatherMap API key"
                    )

                response.raise_for_status()
                logger.info("openweather_current_success", city=city)
                return response.json()

        except HTTPException:
            raise
        except httpx.TimeoutException:
            logger.error("openweather_timeout", city=city)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OpenWeatherMap API timed out"
            )
        except Exception as e:
            logger.error("openweather_current_failed", city=city, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach OpenWeatherMap API"
            )

    async def get_forecast(self, city: str, country_code: str = None, units: str = "metric") -> dict:
        """
        Fetch 5-day weather forecast for a city from OpenWeatherMap API.
        Returns 3-hour interval data for 5 days (40 data points).
        """
        query = f"{city},{country_code}" if country_code else city
        params = {
            "q": query,
            "appid": self.api_key,
            "units": str(units.value) if hasattr(units, 'value') else units,
            "lang": settings.OPENWEATHER_LANG
        }

        logger.info("openweather_forecast_request", city=city, units=units)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("***forcast openweather_request_debug", 
                    url=f"{self.base_url}/weather",
                    params=params,
                    units_value=units
                )

                response = await client.get(
                    f"{self.base_url}/forecast",
                    params=params
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"City '{city}' not found"
                    )

                response.raise_for_status()
                logger.info("openweather_forecast_success", city=city)
                return response.json()

        except HTTPException:
            raise
        except Exception as e:
            logger.error("openweather_forecast_failed", city=city, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach OpenWeatherMap API"
            )

    async def health(self) -> bool:
        """Check OpenWeatherMap API reachability."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={"q": "London", "appid": self.api_key}
                )
                return response.status_code != 0
        except Exception:
            return False


# ── Alternative: WeatherAPI.com ───────────────────────────────────────────────
# from weatherapi import WeatherAPI  (pip install weatherapi)
# client = WeatherAPI(api_key=settings.WEATHERAPI_KEY)
# response = client.current(q="London")
# Supports more data points but requires different response parsing
# ─────────────────────────────────────────────────────────────────────────────

openweather_client = OpenWeatherClient()
