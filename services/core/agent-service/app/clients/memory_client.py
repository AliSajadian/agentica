'''Memory client'''
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryClient:
    """Async HTTP client for memory-service."""

    def __init__(self):
        """Initialise httpx async client."""
        self._client = httpx.AsyncClient(
            base_url=settings.MEMORY_SERVER_URL,
            timeout=settings.HTTP_TIMEOUT,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def get_history(self, session_id: str) -> list[dict]:
        """Fetch conversation history for a session."""
        response = await self._client.post(
            "/api/v1/sessions/history",
            json={"session_id": session_id},
        )
        response.raise_for_status()
        history = response.json().get("messages", [])
        logger.info("memory_get_history", session_id=session_id, count=len(history))
        return history

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def save_message(self, session_id: str, role: str, content: str) -> None:
        """Persist a message to memory-service."""
        response = await self._client.post(
            "/api/v1/sessions/messages",
            json={"session_id": session_id, "role": role, "content": content},
        )
        response.raise_for_status()
        logger.info("memory_save_message", session_id=session_id, role=role)

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
