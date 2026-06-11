# pylint: disable=broad-except
'''Rate limiter'''
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Redis-based sliding window rate limiter per user."""

    def __init__(self):
        """Initialize Redis connection for rate limiting."""
        self.client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW_SECONDS

    async def check(self, user_id: str, endpoint: str) -> bool:
        """
        Check if user has exceeded rate limit for an endpoint.
        Uses Redis INCR with TTL for sliding window counting.
        Raises 429 if limit exceeded.
        """
        key = f"ratelimit:{user_id}:{endpoint}"
        try:
            current = await self.client.incr(key)
            if current == 1:
                await self.client.expire(key, self.window)

            if current > self.max_requests:
                logger.warning(
                    "rate_limit_exceeded",
                    user_id=user_id,
                    endpoint=endpoint,
                    count=current
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {self.max_requests} \
                        requests per {self.window}s"
                )

            logger.info("rate_limit_check", user_id=user_id, count=current)
            return True

        except HTTPException:
            raise
        except Exception as e:
            # fail open — don't block requests if Redis is down
            logger.error("rate_limit_check_failed", error=str(e))
            return True

    async def get_remaining(self, user_id: str, endpoint: str) -> int:
        """Return remaining requests allowed for a user on an endpoint."""
        key = f"ratelimit:{user_id}:{endpoint}"
        try:
            current = await self.client.get(key)
            used = int(current) if current else 0
            return max(0, self.max_requests - used)
        except Exception as e:
            logger.error("rate_limit_remaining_failed", error=str(e))
            return self.max_requests

    async def health(self) -> bool:
        """Check Redis connection health."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


rate_limiter = RateLimiter()
