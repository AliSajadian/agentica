'''
Airports
'''
from fastapi import APIRouter, HTTPException
from app.services.airport import airport_service
from app.models.schemas import (
    AirportSearchRequest, AirportListResponse, AirportResponse
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/search", response_model=AirportListResponse)
async def search_airports(request: AirportSearchRequest):
    """
    Search airports by name, city, IATA code or country.
    Returns list of matching airports with location and timezone info.
    """
    try:
        logger.info("airport_search_started", query=request.query)
        return await airport_service.search(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("airport_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/iata/{iata}", response_model=AirportResponse)
async def get_airport_by_iata(iata: str):
    """
    Get a single airport by its 3-letter IATA code (e.g. LHR, JFK, IKA).
    Returns 404 if airport not found in dataset.
    """
    try:
        return await airport_service.get_by_iata(iata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_airport_failed", iata=iata, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{country}", response_model=AirportListResponse)
async def get_airports_by_country(country: str, limit: int = 20):
    """
    Get all airports in a given country.
    Country name is matched case-insensitively (e.g. 'Iran', 'United States').
    """
    try:
        return await airport_service.search_by_country(country, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_airports_by_country_failed", country=country, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/city/{city}", response_model=AirportListResponse)
async def get_airports_by_city(city: str, limit: int = 10):
    """
    Get all airports in a given city.
    City name is matched case-insensitively (e.g. 'Tehran', 'London').
    """
    try:
        return await airport_service.search_by_city(city, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_airports_by_city_failed", city=city, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
