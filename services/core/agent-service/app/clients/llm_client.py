'''LLM client'''
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LlmClient:
    """Async HTTP client for llm-service."""

    def __init__(self):
        """Initialise httpx async client."""
        self._client = httpx.AsyncClient(
            base_url=settings.LLM_SERVER_URL,
            timeout=settings.HTTP_TIMEOUT,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def rag_answer1(self, question: str, context_chunks: list[str]) -> str:
        """Call llm-service /chat/rag and return the answer string."""
        response = await self._client.post(
            "/api/v1/chat/rag",
            json={"question": question, "context_chunks": context_chunks},
        )
        response.raise_for_status()
        answer = response.json().get("answer", "")
        logger.info("llm_rag_answer", question=question[:60])
        return answer

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def rag_answer(self, question: str, context_chunks: list[str]) -> str:
        """Call llm-service /chat/rag and return the answer string."""
        chunks_payload = [
            {"text": chunk, "score": 1.0, "metadata": {}, "chunk_index": i}
            for i, chunk in enumerate(context_chunks)
        ]
        response = await self._client.post(
            "/api/v1/chat/rag",
            json={"question": question, "context_chunks": chunks_payload},
        )
        response.raise_for_status()
        answer = response.json().get("answer", "")
        logger.info("llm_rag_answer", question=question[:60])
        return answer

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def chat(self, messages: list[dict]) -> str:
        """Call llm-service /chat for multi-turn conversation."""
        response = await self._client.post(
            "/api/v1/chat",
            json={"messages": messages},
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
