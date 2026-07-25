'''Travel agent Config'''
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "travel-agent"
    APP_ENV: str = "development"
    APP_PORT: int = 8010
    DEBUG: bool = True

    # Data paths
    AIRPORTS_DATA_PATH: str = "data/airports.dat"
    ROUTES_DATA_PATH: str = "data/routes.dat"
    AIRLINES_DATA_PATH: str = "data/airlines.dat"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    TRAVEL_CACHE_TTL: int = 1800

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env.docker", case_sensitive=True, extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
