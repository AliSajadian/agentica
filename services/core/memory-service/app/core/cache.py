# pylint: disable=broad-except
'''Cache'''
import redis.asyncio as aioredis
import json
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis cache client for fast session retrieval."""

    def __init__(self):
        """Initialize Redis connection."""
        self.client = None
        # self.client = aioredis.from_url(
        #     settings.REDIS_URL,
        #     decode_responses=True
        # )
        self.ttl = None

    def _get_client(self):
        if self.client is None:
            self.client = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
            self.ttl = settings.REDIS_TTL
        return self.client

    async def get(self, key: str) -> dict | None:
        """Retrieve a cached value by key."""
        try:
            value = await self._get_client().get(key)
            if value:
                logger.info("cache_hit", key=key)
                return json.loads(value)
            logger.info("cache_miss", key=key)
            return None
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: dict, ttl: int = None) -> bool:
        """Store a value in cache with optional TTL."""
        try:
            await self._get_client().setex(
                key,
                ttl or self.ttl,
                json.dumps(value)
            )
            logger.info("cache_set", key=key)
            return True
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached value by key."""
        try:
            await self._get_client().delete(key)
            logger.info("cache_deleted", key=key)
            return True
        except Exception as e:
            logger.error("cache_delete_failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(await self._get_client().exists(key))
        except Exception as e:
            logger.error("cache_exists_failed", key=key, error=str(e))
            return False

    async def health(self) -> bool:
        """Check Redis connection health."""
        try:
            await self._get_client().ping()
            return True
        except Exception:
            return False


redis_cache = RedisCache()
