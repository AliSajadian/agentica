from pydantic_settings import BaseSettings #, SettingsConfigDict
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
    OPENWEATHER_API_KEY: str = "bc3fd8b7cbc771df346c6a812905fb7d"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_UNITS: str = "metric"
    OPENWEATHER_LANG: str = "en"

    # Redis Cache
    REDIS_HOST: str = "redis-weather-svc.agentica-app.svc.cluster.local"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    WEATHER_CACHE_TTL: int = 1800

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env.docker", case_sensitive=True)
    # model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8", extra='ignore')

@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
