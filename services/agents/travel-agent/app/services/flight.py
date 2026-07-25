'''
Flight service
'''
import json
import redis.asyncio as aioredis
from fastapi import HTTPException, status


from app.config import settings
from app.utils.logger import get_logger
from app.core.openflights import openflights_data
from app.models.schemas import (
    FlightSearchRequest, FlightSearchResponse,
    RouteResponse, DeparturesRequest, DeparturesResponse,
    ArrivalsRequest, ArrivalsResponse,
    TravelSummaryRequest, TravelSummaryResponse
)


logger = get_logger(__name__)

CACHE_PREFIX = "travel:flight:"


class FlightService:
    """Service for searching flight routes from the OpenFlights static dataset."""

    def __init__(self):
        """Initialize Redis cache client."""
        self.cache = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.ttl = settings.TRAVEL_CACHE_TTL

    async def search_routes(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """
        Search all direct routes between two airports by IATA code.
        Validates both airports exist before querying routes.
        """
        origin = request.origin.upper()
        dest = request.destination.upper()
        cache_key = f"{CACHE_PREFIX}routes:{origin}:{dest}:{request.limit}"

        cached = await self._get_cache(cache_key)
        if cached:
            return FlightSearchResponse(**cached)

        if not openflights_data.get_airport_by_iata(origin):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origin airport '{origin}' not found"
            )
        if not openflights_data.get_airport_by_iata(dest):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination airport '{dest}' not found"
            )

        raw_routes = openflights_data.search_routes(origin, dest, request.limit)
        routes = [self._parse_route(r) for r in raw_routes]

        result = FlightSearchResponse(
            origin=origin,
            destination=dest,
            total_routes=len(routes),
            routes=routes
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("routes_search_done", origin=origin, dest=dest, total=len(routes))
        return result

    async def get_departures(self, request: DeparturesRequest) -> DeparturesResponse:
        """
        Get all routes departing from a given airport.
        Validates airport exists before querying.
        """
        iata = request.iata.upper()
        cache_key = f"{CACHE_PREFIX}departures:{iata}:{request.limit}"

        cached = await self._get_cache(cache_key)
        if cached:
            return DeparturesResponse(**cached)

        if not openflights_data.get_airport_by_iata(iata):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport '{iata}' not found"
            )

        raw_routes = openflights_data.get_routes_from(iata, request.limit)
        routes = [self._parse_route(r) for r in raw_routes]

        result = DeparturesResponse(
            airport_iata=iata,
            total_routes=len(routes),
            routes=routes
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("departures_done", iata=iata, total=len(routes))
        return result

    async def get_arrivals(self, request: ArrivalsRequest) -> ArrivalsResponse:
        """
        Get all routes arriving at a given airport.
        Validates airport exists before querying.
        """
        iata = request.iata.upper()
        cache_key = f"{CACHE_PREFIX}arrivals:{iata}:{request.limit}"

        cached = await self._get_cache(cache_key)
        if cached:
            return ArrivalsResponse(**cached)

        if not openflights_data.get_airport_by_iata(iata):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport '{iata}' not found"
            )

        raw_routes = openflights_data.get_routes_to(iata, request.limit)
        routes = [self._parse_route(r) for r in raw_routes]

        result = ArrivalsResponse(
            airport_iata=iata,
            total_routes=len(routes),
            routes=routes
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("arrivals_done", iata=iata, total=len(routes))
        return result

    async def get_travel_summary(
        self,
        request: TravelSummaryRequest
    ) -> TravelSummaryResponse:
        """
        Build natural language travel summary for agent-service.
        Combines airport info and route availability into a readable string.
        """
        origin = request.origin.upper()
        dest = request.destination.upper()
        cache_key = f"{CACHE_PREFIX}summary:{origin}:{dest}"

        cached = await self._get_cache(cache_key)
        if cached:
            return TravelSummaryResponse(**cached)

        origin_raw = openflights_data.get_airport_by_iata(origin)
        dest_raw = openflights_data.get_airport_by_iata(dest)
        raw_routes = openflights_data.search_routes(origin, dest, 50)

        # collect unique non-null airline codes
        airlines = list({
            str(r["airline"])
            for r in raw_routes
            if r.get("airline") and str(r["airline"]) not in ("nan", "\\N", "")
        })

        origin_name = (
            f"{origin_raw['name']}, {origin_raw['city']}, {origin_raw['country']}"
            if origin_raw else origin
        )
        dest_name = (
            f"{dest_raw['name']}, {dest_raw['city']}, {dest_raw['country']}"
            if dest_raw else dest
        )

        if raw_routes:
            airline_str = ", ".join(airlines[:5])
            more = f" and {len(airlines) - 5} more" if len(airlines) > 5 else ""
            summary = (
                f"Route from {origin_name} ({origin}) to {dest_name} ({dest}): "
                f"{len(raw_routes)} direct route(s) found, "
                f"operated by airlines: {airline_str}{more}."
            )
        else:
            summary = (
                f"No direct routes found from {origin_name} ({origin}) "
                f"to {dest_name} ({dest}) in the OpenFlights dataset. "
                f"Consider checking connecting flights via a hub airport."
            )

        # build airport response objects
        from app.services.airport import airport_service

        origin_airport = None
        dest_airport = None

        if origin_raw:
            try:
                origin_airport = await airport_service.get_by_iata(origin)
            except Exception:
                pass
        if dest_raw:
            try:
                dest_airport = await airport_service.get_by_iata(dest)
            except Exception:
                pass

        result = TravelSummaryResponse(
            origin=origin,
            destination=dest,
            origin_airport=origin_airport,
            destination_airport=dest_airport,
            total_routes=len(raw_routes),
            airlines_serving=airlines,
            summary=summary
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("travel_summary_done", origin=origin, dest=dest, routes=len(raw_routes))
        return result

    def _parse_route(self, raw: dict) -> RouteResponse:
        """Parse raw OpenFlights route dict into RouteResponse schema."""
        def safe_str(val):
            """Safely convert value to string, returning None for nan."""
            if val is None:
                return None
            s = str(val)
            return None if s in ("nan", "\\N", "") else s

        def safe_int(val):
            """Safely convert value to int."""
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        return RouteResponse(
            airline=safe_str(raw.get("airline")),
            airline_id=safe_str(raw.get("airline_id")),
            source_airport=safe_str(raw.get("source_airport")),
            dest_airport=safe_str(raw.get("dest_airport")),
            codeshare=safe_str(raw.get("codeshare")),
            stops=safe_int(raw.get("stops")),
            equipment=safe_str(raw.get("equipment")),
        )

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve cached flight data from Redis."""
        try:
            value = await self.cache.get(key)
            if value:
                logger.info("flight_cache_hit", key=key)
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("flight_cache_get_failed", error=str(e))
            return None

    async def _set_cache(self, key: str, value: dict):
        """Store flight data in Redis with TTL."""
        try:
            await self.cache.setex(key, self.ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error("flight_cache_set_failed", error=str(e))


flight_service = FlightService()
