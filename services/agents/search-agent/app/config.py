from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "search-agent"
    APP_ENV: str = "development"
    APP_PORT: int = 8012
    DEBUG: bool = True

    # Search
    SEARCH_PROVIDER: str = "tavily"

    # Tavily
    TAVILY_API_KEY: str

    # Shared
    TIMEOUT: int = 30

    # Tavily Search API
    TAVILY_BASE_URL: str = "https://api.tavily.com"

    # Brave Search API
    BRAVE_API_KEY: str
    BRAVE_BASE_URL: str = "https://api.search.brave.com/res/v1"
    BRAVE_SAFESEARCH: str = "moderate"
    BRAVE_COUNT: int = 10

    # DuckDuckGo Search API 
    DUCKDUCKGO_BASE_URL: str = "https://api.duckduckgo.com"

    # Redis Cache
    REDIS_HOST: str = "redis-search"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 3
    SEARCH_CACHE_TTL: int = 300

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env.docker",
        # secrets_dir=Path(__file__).parent.parent / "secrets", 
        secrets_dir="/home/ali/projects/AI/agentica/services/agents/search-agent/secrets",
        # secrets_dir="/app/secrets",
        case_sensitive=True
    )

@lru_cache
def get_setting() -> Settings:
    '''Return cached settings instance'''
    return Settings()

settings = get_setting()