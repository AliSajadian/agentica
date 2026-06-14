'''Rag client'''
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RagClient:
    """Async HTTP client for rag-service."""

    def __init__(self):
        """Initialise httpx async client."""
        self._client = httpx.AsyncClient(
            base_url=settings.RAG_SERVER_URL,
            timeout=settings.HTTP_TIMEOUT,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def search(self, query: str, limit: int = 5) -> list[str]:
        """Search rag-service and return top context chunks."""
        response = await self._client.post(
            "/api/v1/search",
            json={"query": query, "limit": limit},
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        chunks = [r["text"] for r in results]
        logger.info("rag_search", query=query, chunks_returned=len(chunks))
        return chunks

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
