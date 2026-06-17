from fastapi import APIRouter, HTTPException
from app.services.search import search_service
from app.models.schemas import (
    SearchRequest, SearchResponse,
    NewsRequest, NewsResponse,
    SearchSummaryRequest, SearchSummaryResponse
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/web", response_model=SearchResponse)
async def web_search(request: SearchRequest):
    """
    Perform a web search for a query.
    Returns list of relevant results with titles, URLs and descriptions.
    """
    try:
        logger.info("web_search_started", query=request.query)
        return await search_service.search(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("web_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news", response_model=NewsResponse)
async def news_search(request: NewsRequest):
    """
    Search for recent news articles on a topic.
    Returns news results with source and publication info.
    """
    try:
        logger.info("news_search_started", query=request.query)
        return await search_service.search_news(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("news_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=SearchSummaryResponse)
async def search_summary(request: SearchSummaryRequest):
    """
    Get natural language search summary for agent-service.
    Combines top results into a human-readable summary string.
    """
    try:
        logger.info("search_summary_started", query=request.query)
        return await search_service.get_summary(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("search_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
