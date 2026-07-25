'''
Airline service
'''
import json
from fastapi import HTTPException, status
import redis.asyncio as aioredis
from app.core.openflights import openflights_data
from app.models.schemas import AirlineResponse, AirlineListResponse, AirlineSearchRequest
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_PREFIX = "travel:airline:"


class AirlineService:
    """Service for searching and retrieving airline data from OpenFlights dataset."""

    def __init__(self):
        """Initialize Redis cache client."""
        self.cache = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.ttl = settings.TRAVEL_CACHE_TTL

    async def search(self, request: AirlineSearchRequest) -> AirlineListResponse:
        """
        Search airlines by name, IATA code or country.
        Returns only active airlines from the dataset.
        """
        cache_key = f"{CACHE_PREFIX}search:{request.query.lower()}:{request.limit}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirlineListResponse(**cached)

        raw = openflights_data.search_airlines(request.query, request.limit)
        airlines = [self._parse(a) for a in raw]

        result = AirlineListResponse(
            query=request.query,
            total=len(airlines),
            airlines=airlines
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airline_search_done", query=request.query, total=len(airlines))
        return result

    async def get_by_iata(self, iata: str) -> AirlineResponse:
        """
        Get a single airline by its 2-letter IATA code.
        Raises 404 if airline not found or inactive.
        """
        cache_key = f"{CACHE_PREFIX}iata:{iata.upper()}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirlineResponse(**cached)

        raw = openflights_data.get_airline_by_iata(iata)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airline with IATA code '{iata.upper()}' not found"
            )

        result = self._parse(raw)
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airline_fetched", iata=iata.upper())
        return result

    async def get_by_country(self, country: str, limit: int = 20) -> AirlineListResponse:
        """
        Get all active airlines registered in a given country.
        Returns cached results if available.
        """
        cache_key = f"{CACHE_PREFIX}country:{country.lower()}:{limit}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirlineListResponse(**cached)

        raw = openflights_data.get_airlines_by_country(country, limit)
        airlines = [self._parse(a) for a in raw]
        result = AirlineListResponse(
            query=country,
            total=len(airlines),
            airlines=airlines
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airlines_by_country_done", country=country, total=len(airlines))
        return result

    def _parse(self, raw: dict) -> AirlineResponse:
        """Parse raw OpenFlights airline dict into AirlineResponse schema."""
        def safe_int(val):
            """Safely convert value to int."""
            try:
                return int(float(str(val)))
            except (ValueError, TypeError):
                return None

        def safe_str(val):
            """Safely convert value to string, returning None for nan."""
            if val is None:
                return None
            s = str(val)
            return None if s in ("nan", "\\N", "") else s

        return AirlineResponse(
            id=safe_int(raw.get("id")),
            name=safe_str(raw.get("name")),
            alias=safe_str(raw.get("alias")),
            iata=safe_str(raw.get("iata")),
            icao=safe_str(raw.get("icao")),
            callsign=safe_str(raw.get("callsign")),
            country=safe_str(raw.get("country")),
            active=safe_str(raw.get("active")),
        )

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve cached airline data from Redis."""
        try:
            value = await self.cache.get(key)
            if value:
                logger.info("airline_cache_hit", key=key)
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("airline_cache_get_failed", error=str(e))
            return None

    async def _set_cache(self, key: str, value: dict):
        """Store airline data in Redis with TTL."""
        try:
            await self.cache.setex(key, self.ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error("airline_cache_set_failed", error=str(e))


airline_service = AirlineService()
