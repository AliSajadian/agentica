# pylint: disable=broad-except
'''Ollama'''
import httpx
import json
from app.config import settings
from app.utils.logger import get_logger
from typing import AsyncGenerator

logger = get_logger(__name__)

OLLAMA_BASE_URL = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"


class OllamaClient:
    '''Ollama Client'''
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def generate(self, prompt: str) -> str:
        """Single response generation — no streaming."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.TEMPERATURE,
                        "top_p": settings.TOP_P,
                        "num_predict": settings.MAX_TOKENS,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info("ollama_generate_done", model=self.model)
            return data["response"]

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streaming generation — yields tokens one by one."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": settings.TEMPERATURE,
                        "top_p": settings.TOP_P,
                        "num_predict": settings.MAX_TOKENS,
                    }
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if not chunk.get("done", False):
                            yield chunk.get("response", "")

    async def chat(self, messages: list[dict]) -> str:
        """Chat completion — takes message history."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": settings.TEMPERATURE,
                        "top_p": settings.TOP_P,
                        "num_predict": settings.MAX_TOKENS,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info("ollama_chat_done", model=self.model)
            return data["message"]["content"]

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Streaming chat — yields tokens one by one."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": settings.TEMPERATURE,
                        "top_p": settings.TOP_P,
                        "num_predict": settings.MAX_TOKENS,
                    }
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if not chunk.get("done", False):
                            yield chunk["message"].get("content", "")

    async def health(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available local models."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]


# ── GPU alternative note ──────────────────────────────────────────────────────
# Ollama automatically uses GPU if available (NVIDIA CUDA or Apple Metal)
# On your Intel UHD 620, it runs on CPU automatically — no config needed
# To force CPU: set OLLAMA_NUM_GPU=0 in environment
# ─────────────────────────────────────────────────────────────────────────────

ollama_client = OllamaClient()
