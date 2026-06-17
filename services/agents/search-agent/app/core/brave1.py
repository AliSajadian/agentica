import httpx
from app.config import settings
from app.utils.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger(__name__)


class DuckDuckGoClient:
    """
    HTTP client for DuckDuckGo search using the unofficial API.
    No API key required — free for development use.
    Swap this class for BraveClient or TavilyClient in production.
    """

    def __init__(self):
        """Initialize DuckDuckGo client."""
        self.base_url = settings.DUCKDUCKGO_BASE_URL
        self.timeout = settings.TIMEOUT

    async def search(self, query: str, count: int = 10) -> dict:
        """
        Search the web using DuckDuckGo instant answer API.
        Returns structured results from DuckDuckGo.
        """
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
            "no_redirect": "1"
        }

        logger.info("duckduckgo_search_request", query=query)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                logger.info("duckduckgo_search_success", query=query)
                return response.json()

        except httpx.TimeoutException:
            logger.error("duckduckgo_timeout", query=query)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="DuckDuckGo API timed out"
            )
        except Exception as e:
            logger.error("duckduckgo_search_failed", query=query, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach search API"
            )

    async def health(self) -> bool:
        """Check DuckDuckGo API reachability."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    self.base_url,
                    params={"q": "test", "format": "json"}
                )
                return response.status_code == 200
        except Exception:
            return False


# ── Brave Search alternative (requires API key) ───────────────────────────────
# class BraveClient:
#     def __init__(self):
#         self.base_url = "https://api.search.brave.com/res/v1"
#         self.api_key = settings.BRAVE_API_KEY
#         self.timeout = 30
#
#     async def search(self, query: str, count: int = 10) -> dict:
#         headers = {
#             "Accept": "application/json",
#             "Accept-Encoding": "gzip",
#             "X-Subscription-Token": self.api_key
#         }
#         params = {
#             "q": query,
#             "count": count,
#             "safesearch": settings.BRAVE_SAFESEARCH
#         }
#         async with httpx.AsyncClient(timeout=self.timeout) as client:
#             response = await client.get(
#                 f"{self.base_url}/web/search",
#                 headers=headers,
#                 params=params
#             )
#             response.raise_for_status()
#             return response.json()
# ─────────────────────────────────────────────────────────────────────────────

# ── Tavily alternative (1000 free/month) ─────────────────────────────────────
# pip install tavily-python
# from tavily import TavilyClient
# client = TavilyClient(api_key=settings.TAVILY_API_KEY)
# results = client.search(query="your query", max_results=10)
# ─────────────────────────────────────────────────────────────────────────────

search_client = DuckDuckGoClient()