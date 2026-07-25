'''
Flights
'''
from fastapi import APIRouter, HTTPException
from app.services.flight import flight_service
from app.models.schemas import FlightSearchRequest, FlightSearchResponse, DeparturesRequest, DeparturesResponse, \
    ArrivalsRequest, ArrivalsResponse, TravelSummaryRequest, TravelSummaryResponse

from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/search", response_model=FlightSearchResponse)
async def search_flights(request: FlightSearchRequest):
    """
    Search all direct routes between two airports by IATA code.
    Returns list of airlines and aircraft equipment serving this route.
    """
    try:
        logger.info(
            "flight_search_started",
            origin=request.origin,
            destination=request.destination
        )
        return await flight_service.search_routes(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("flight_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/departures", response_model=DeparturesResponse)
async def get_departures(request: DeparturesRequest):
    """
    Get all routes departing from a given airport.
    Returns all destinations reachable from this airport with airline info.
    """
    try:
        logger.info("departures_started", iata=request.iata)
        return await flight_service.get_departures(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("departures_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/arrivals", response_model=ArrivalsResponse)
async def get_arrivals(request: ArrivalsRequest):
    """
    Get all routes arriving at a given airport.
    Returns all origins that fly into this airport with airline info.
    """
    try:
        logger.info("arrivals_started", iata=request.iata)
        return await flight_service.get_arrivals(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("arrivals_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=TravelSummaryResponse)
async def get_travel_summary(request: TravelSummaryRequest):
    """
    Get natural language travel summary for agent-service.
    Combines airport info and route data into a human-readable summary string.
    """
    try:
        logger.info(
            "travel_summary_started",
            origin=request.origin,
            destination=request.destination
        )
        return await flight_service.get_travel_summary(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("travel_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
