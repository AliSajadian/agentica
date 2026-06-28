from ddgs import DDGS
from app.utils.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger(__name__)


class DuckDuckGoClient:
    """
    Search client using duckduckgo-search library.
    No API key required — free unlimited searches.
    """

    async def search(self, query: str, count: int = 10) -> list[dict]:
        """Search the web using DuckDuckGo and return raw results."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=count
                ))
            logger.info("duckduckgo_search_success", query=query, count=len(results))
            return results
        except Exception as e:
            logger.error("duckduckgo_search_failed", query=query, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Search failed: {str(e)}"
            )

    async def search_news(self, query: str, count: int = 10) -> list[dict]:
        """Search for news articles using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    query,
                    max_results=count
                ))
            logger.info("duckduckgo_news_success", query=query, count=len(results))
            return results
        except Exception as e:
            logger.error("duckduckgo_news_failed", query=query, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"News search failed: {str(e)}"
            )

    async def health(self) -> bool:
        """Check DuckDuckGo search availability."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text("test", max_results=1))
                return len(results) > 0
        except Exception:
            return False


search_client = DuckDuckGoClient()
