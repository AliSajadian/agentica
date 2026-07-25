# pylint: disable=broad-except
'''
Airports service
'''
import json
from fastapi import HTTPException, status
import redis.asyncio as aioredis
from app.core.openflights import openflights_data
from app.models.schemas import AirportResponse, AirportListResponse, AirportSearchRequest
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_PREFIX = "travel:airport:"


class AirportService:
    """Service for searching and retrieving airport data from OpenFlights dataset."""

    def __init__(self):
        """Initialize Redis cache client."""
        self.cache = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.ttl = settings.TRAVEL_CACHE_TTL

    async def search(self, request: AirportSearchRequest) -> AirportListResponse:
        """
        Search airports by name, city, IATA code or country.
        Returns cached results if available, otherwise queries OpenFlights data.
        """
        cache_key = f"{CACHE_PREFIX}search:{request.query.lower()}:{request.limit}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirportListResponse(**cached)

        raw = openflights_data.search_airports(request.query, request.limit)
        airports = [self._parse(a) for a in raw]

        result = AirportListResponse(
            query=request.query,
            total=len(airports),
            airports=airports
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airport_search_done", query=request.query, total=len(airports))
        return result

    async def get_by_iata(self, iata: str) -> AirportResponse:
        """
        Get a single airport by IATA code.
        Raises 404 if airport not found in dataset.
        """
        cache_key = f"{CACHE_PREFIX}iata:{iata.upper()}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirportResponse(**cached)

        raw = openflights_data.get_airport_by_iata(iata)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport with IATA code '{iata.upper()}' not found"
            )

        result = self._parse(raw)
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airport_fetched", iata=iata.upper())
        return result

    async def search_by_country(self, country: str, limit: int = 20) -> AirportListResponse:
        """
        Get all airports in a given country.
        Returns cached results if available.
        """
        cache_key = f"{CACHE_PREFIX}country:{country.lower()}:{limit}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirportListResponse(**cached)

        raw = openflights_data.search_airports_by_country(country, limit)
        airports = [self._parse(a) for a in raw]
        result = AirportListResponse(
            query=country,
            total=len(airports),
            airports=airports
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airports_by_country_done", country=country, total=len(airports))
        return result

    async def search_by_city(self, city: str, limit: int = 10) -> AirportListResponse:
        """
        Get all airports in a given city.
        Returns cached results if available.
        """
        cache_key = f"{CACHE_PREFIX}city:{city.lower()}:{limit}"
        cached = await self._get_cache(cache_key)
        if cached:
            return AirportListResponse(**cached)

        raw = openflights_data.search_airports_by_city(city, limit)
        airports = [self._parse(a) for a in raw]
        result = AirportListResponse(
            query=city,
            total=len(airports),
            airports=airports
        )
        await self._set_cache(cache_key, result.model_dump())
        logger.info("airports_by_city_done", city=city, total=len(airports))
        return result

    def _parse(self, raw: dict) -> AirportResponse:
        """Parse raw OpenFlights airport dict into AirportResponse schema."""
        def safe_int(val):
            """Safely convert value to int."""
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        def safe_float(val):
            """Safely convert value to float."""
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def safe_str(val):
            """Safely convert value to string, returning None for nan."""
            if val is None:
                return None
            s = str(val)
            return None if s in ("nan", "\\N", "") else s

        return AirportResponse(
            id=safe_int(raw.get("id")),
            name=safe_str(raw.get("name")),
            city=safe_str(raw.get("city")),
            country=safe_str(raw.get("country")),
            iata=safe_str(raw.get("iata")),
            icao=safe_str(raw.get("icao")),
            latitude=safe_float(raw.get("latitude")),
            longitude=safe_float(raw.get("longitude")),
            altitude=safe_float(raw.get("altitude")),
            timezone=safe_float(raw.get("timezone")),
        )

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve cached airport data from Redis."""
        try:
            value = await self.cache.get(key)
            if value:
                logger.info("airport_cache_hit", key=key)
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("airport_cache_get_failed", error=str(e))
            return None

    async def _set_cache(self, key: str, value: dict):
        """Store airport data in Redis with TTL."""
        try:
            await self.cache.setex(key, self.ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error("airport_cache_set_failed", error=str(e))


airport_service = AirportService()
