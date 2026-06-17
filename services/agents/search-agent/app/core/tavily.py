from abc import ABC, abstractmethod
import asyncio

from tavily import TavilyClient as TavilySDKClient
from fastapi import HTTPException, status

from app.core.search_provider import SearchProvider
from app.config import settings
from app.models.schemas import SearchResult, NewsResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TavilyClient(SearchProvider):

    def __init__(self):
        logger.info(f"settings.TAVILY_API_KEY: {settings.TAVILY_API_KEY}")
        self.client = TavilySDKClient(
            api_key=settings.TAVILY_API_KEY,
            # api_base_url=settings.TAVILY_BASE_URL
        )

    async def _search_tavily(
        self,
        query: str,
        count: int,
        topic: str = "general"
    ):
        return await asyncio.to_thread(
            self.client.search,
            query=query,
            max_results=count,
            topic=topic,
        )

    async def search(
        self,
        query: str,
        count: int = 10,
    ) -> list[SearchResult]:

        logger.info("tavily_search_request", query=query)

        try:
            response = await asyncio.to_thread(
                self.client.search,
                query=query,
                max_results=count,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
            )

            # return {
            #     "query": query,
            #     "provider": "tavily",
            #     "answer": result.get("answer"),
            #     "results": [
            #         {
            #             "title": item.get("title"),
            #             "url": item.get("url"),
            #             "snippet": item.get("content"),
            #             "score": item.get("score"),
            #         }
            #         for item in result.get("results", [])
            #     ],
            # }
        
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    description=item.get("content", ""),
                    source="Tavily"
                )
                for item in response.get("results", [])
            ]
        
        except Exception as e:
            logger.error(
                "tavily_search_failed",
                query=query,
                error=str(e),
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach Tavily API",
            )

    async def search_news(
        self,
        query: str,
        count: int = 10,
    ) -> list[NewsResult]:

        logger.info("tavily_search_request", query=query)

        try:
            response = await asyncio.to_thread(
                self.client.search,
                query=f"{query} news",
                max_results=count,
                search_depth="advanced",
            )

            return [
                NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    description=item.get("content", ""),
                    source="Tavily",
                )
                for item in response.get("results", [])
            ]


        except Exception as e:
            logger.error(
                "tavily_search_failed",
                query=query,
                error=str(e),
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach Tavily API",
            )

    async def health(self) -> bool:
        try:
            await asyncio.to_thread(
                self.client.search,
                query="health check",
                max_results=1,
            )
            return True
        except Exception:
            return False


search_client = TavilyClient()
