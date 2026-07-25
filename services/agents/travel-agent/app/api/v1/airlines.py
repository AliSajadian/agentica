'''
Airlines
'''
from fastapi import APIRouter, HTTPException
from app.services.airline import airline_service
from app.models.schemas import (
    AirlineSearchRequest, AirlineListResponse, AirlineResponse
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/search", response_model=AirlineListResponse)
async def search_airlines(request: AirlineSearchRequest):
    """
    Search active airlines by name, IATA code or country.
    Returns only airlines marked as active in the OpenFlights dataset.
    """
    try:
        logger.info("airline_search_started", query=request.query)
        return await airline_service.search(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("airline_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/iata/{iata}", response_model=AirlineResponse)
async def get_airline_by_iata(iata: str):
    """
    Get a single airline by its 2-letter IATA code (e.g. BA, QR, W5).
    Returns 404 if airline not found or inactive.
    """
    try:
        return await airline_service.get_by_iata(iata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_airline_failed", iata=iata, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/country/{country}", response_model=AirlineListResponse)
async def get_airlines_by_country(country: str, limit: int = 20):
    """
    Get all active airlines registered in a given country.
    Country name is matched case-insensitively (e.g. 'Iran', 'United Kingdom').
    """
    try:
        return await airline_service.get_by_country(country, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_airlines_by_country_failed", country=country, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
