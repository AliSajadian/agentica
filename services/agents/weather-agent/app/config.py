from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "weather-agent"
    APP_ENV: str = "development"
    APP_PORT: int = 8011
    DEBUG: bool = True

    # OpenWeatherMap
    OPENWEATHER_API_KEY: str = "your-openweathermap-api-key"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_UNITS: str = "metric"
    OPENWEATHER_LANG: str = "en"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    WEATHER_CACHE_TTL: int = 1800

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
