import json
import redis.asyncio as aioredis
from app.core.tavily import search_client
from app.models.schemas import (
    SearchRequest, SearchResponse, SearchResult,
    NewsRequest, NewsResponse, NewsResult,
    SearchSummaryRequest, SearchSummaryResponse
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_PREFIX_SEARCH = "search:web:"
CACHE_PREFIX_NEWS = "search:news:"


class SearchService:
    """Orchestrates search queries, caching and result formatting."""

    def __init__(self):
        """Initialize Redis cache client."""
        self.cache = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.ttl = settings.SEARCH_CACHE_TTL

    async def search1(self, request: SearchRequest) -> SearchResponse:
        """
        Perform web search for a query.
        Returns cached result if available, otherwise fetches from API.
        """
        cache_key = f"{CACHE_PREFIX_SEARCH}{request.query}:{request.count}"

        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return SearchResponse(**cached)

        data = await search_client.search(
            query=request.query,
            count=request.count
        )

        results = self._parse_results(data)
        response = SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results[:request.count],
            search_type=request.search_type.value,
            cached=False
        )

        await self._set_cache(cache_key, response.model_dump())
        logger.info("search_completed", query=request.query, results=len(results))
        return response

    async def search_news1(self, request: NewsRequest) -> NewsResponse:
        """
        Search for news articles on a topic.
        Appends 'news' to query for better news results from DuckDuckGo.
        """
        news_query = f"{request.query} news"
        cache_key = f"{CACHE_PREFIX_NEWS}{news_query}:{request.count}"

        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return NewsResponse(**cached)

        data = await search_client.search(
            query=news_query,
            count=request.count
        )

        results = self._parse_news_results(data)
        response = NewsResponse(
            query=request.query,
            total_results=len(results),
            results=results[:request.count],
            cached=False
        )

        await self._set_cache(cache_key, response.model_dump())
        logger.info("news_search_completed", query=request.query, results=len(results))
        return response

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform web search, cache and return results."""
        cache_key = f"{CACHE_PREFIX_SEARCH}{request.query}:{request.count}"

        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return SearchResponse(**cached)

        results = await search_client.search(          # returns list now
            query=request.query,
            count=request.count
        )

        # results = self._parse_results(data)         # pass list directly
        response = SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            search_type=request.search_type.value,
            cached=False
        )

        await self._set_cache(cache_key, response.model_dump())
        return response

    async def search_news(self, request: NewsRequest) -> NewsResponse:
        """Search news, cache and return results."""
        cache_key = f"{CACHE_PREFIX_NEWS}{request.query}:{request.count}"

        cached = await self._get_cache(cache_key)
        if cached:
            cached["cached"] = True
            return NewsResponse(**cached)

        results = await search_client.search_news(     # returns list now
            query=request.query,
            count=request.count
        )

        # results = self._parse_news_results(data)    # pass list directly
        response = NewsResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            cached=False
        )

        await self._set_cache(cache_key, response.model_dump())
        return response

    async def get_summary(self, request: SearchSummaryRequest) -> SearchSummaryResponse:
        """
        Get natural language search summary for agent-service consumption.
        Combines top results into a human-readable summary string.
        """
        search_request = SearchRequest(
            query=request.query,
            count=request.count,
            search_type=request.search_type
        )
        search_response = await self.search(search_request)

        if not search_response.results:
            summary = f"No results found for '{request.query}'."
        else:
            top_results = search_response.results[:3]
            summary = f"Top results for '{request.query}':\n"
            summary += "\n".join(
                f"{i+1}. {r.title} — {r.description[:100]}... ({r.url})"
                for i, r in enumerate(top_results)
            )

        logger.info("search_summary_built", query=request.query)
        return SearchSummaryResponse(
            query=request.query,
            summary=summary,
            results=search_response.results,
            total=search_response.total_results
        )

    def _parse_results1(self, data: dict) -> list[SearchResult]:
        """Parse DuckDuckGo API response into list of SearchResult."""
        results = []

        # abstract text (main result)
        if data.get("AbstractText") and data.get("AbstractURL"):
            results.append(SearchResult(
                title=data.get("Heading", "Result"),
                url=data["AbstractURL"],
                description=data["AbstractText"],
                source=data.get("AbstractSource")
            ))

        # related topics
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("FirstURL"):
                text = topic.get("Text", "")
                results.append(SearchResult(
                    title=text[:60] if text else "Related",
                    url=topic["FirstURL"],
                    description=text,
                    source="DuckDuckGo"
                ))

        return results

    def _parse_news_results1(self, data: dict) -> list[NewsResult]:
        """Parse DuckDuckGo API response into list of NewsResult."""
        results = []
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("FirstURL"):
                text = topic.get("Text", "")
                icon = topic.get("Icon", {})
                results.append(NewsResult(
                    title=text[:80] if text else "News",
                    url=topic["FirstURL"],
                    description=text,
                    source="DuckDuckGo",
                    thumbnail=icon.get("URL") if icon else None
                ))
        return results

    def _parse_results(self, data: list[dict]) -> list[SearchResult]:
        """Parse duckduckgo-search results into list of SearchResult."""
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                description=r.get("body", ""),
                source=r.get("source", "DuckDuckGo"),
                published_date=None
            )
            for r in data if r.get("href")
        ]

    def _parse_news_results(self, data: list[dict]) -> list[NewsResult]:
        """Parse duckduckgo-search news results into list of NewsResult."""
        return [
            NewsResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                description=r.get("body", ""),
                source=r.get("source", "DuckDuckGo"),
                published_date=r.get("date"),
                thumbnail=r.get("image")
            )
            for r in data if r.get("url")
        ]

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve cached search results from Redis."""
        try:
            value = await self.cache.get(key)
            if value:
                logger.info("search_cache_hit", key=key)
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("search_cache_get_failed", error=str(e))
            return None

    async def _set_cache(self, key: str, value: dict):
        """Store search results in Redis with TTL."""
        try:
            await self.cache.setex(key, self.ttl, json.dumps(value))
        except Exception as e:
            logger.error("search_cache_set_failed", error=str(e))


search_service = SearchService()
