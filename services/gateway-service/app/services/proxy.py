# pylint: disable=broad-except
'''Proxy'''
import httpx
from fastapi import HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# map service names to their base URLs
SERVICE_MAP = {
    "rag": settings.RAG_SERVICE_URL,
    "llm": settings.LLM_SERVICE_URL,
    "memory": settings.MEMORY_SERVICE_URL,
    "agent": settings.AGENT_SERVICE_URL,
}


class ProxyService:
    """Forwards authenticated requests to upstream microservices."""

    async def forward(
        self,
        service: str,
        path: str,
        method: str,
        payload: dict = None,
        headers: dict = None,
        user_id: str = None
    ) -> dict:
        """
        Forward a request to an upstream service.
        Injects X-User-ID header for downstream service identification.
        Raises 404 if service unknown, 502 if upstream unreachable.
        """
        base_url = SERVICE_MAP.get(service)
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown service: {service}"
            )

        url = f"{base_url}{path}"
        forward_headers = {"Content-Type": "application/json"}

        # inject user identity for downstream services
        if user_id:
            forward_headers["X-User-ID"] = user_id

        if headers:
            forward_headers.update(headers)

        logger.info("proxy_forwarding", service=service, path=path, method=method)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=forward_headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as e:
            logger.error("proxy_timeout", service=service, url=url)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {service} timed out"
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error("proxy_upstream_error", service=service, status=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            ) from e
        except Exception as e:
            logger.error("proxy_failed", service=service, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service {service} unreachable"
            ) from e

    async def health_check_all(self) -> dict:
        """Check health of all upstream services."""
        results = {}
        for name, base_url in SERVICE_MAP.items():
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{base_url}/health")
                    results[name] = "ok" if response.status_code == 200 else "error"
            except Exception:
                results[name] = "unreachable"
        return results


proxy_service = ProxyService()
