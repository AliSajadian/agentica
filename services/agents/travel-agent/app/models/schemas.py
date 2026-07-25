'''
Schemas AirportResponse, AirportListResponse, AirportSearchRequest
'''
from typing import Optional
from pydantic import BaseModel, Field


# ── Airport schemas ───────────────────────────────────────────────────────────

class AirportSearchRequest(BaseModel):
    """Schema for airport search by name, city, IATA code or country."""
    query: str = Field(..., min_length=2, description="City, airport name, IATA code or country")
    limit: int = Field(default=10, ge=1, le=50)


class AirportResponse(BaseModel):
    """Schema for a single airport result."""
    id: Optional[int] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    iata: Optional[str] = None
    icao: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    timezone: Optional[float] = None


class AirportListResponse(BaseModel):
    """Schema for airport search results list."""
    query: str
    total: int
    airports: list[AirportResponse]


# ── Route / Flight schemas ────────────────────────────────────────────────────

class FlightSearchRequest(BaseModel):
    """Schema for searching routes between two airports by IATA code."""
    origin: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Origin airport IATA code e.g. IKA, LHR, JFK"
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Destination airport IATA code e.g. DXB, CDG, IST"
    )
    limit: int = Field(default=20, ge=1, le=100)


class RouteResponse(BaseModel):
    """Schema for a single flight route from the OpenFlights dataset."""
    airline: Optional[str] = None
    airline_id: Optional[str] = None
    source_airport: Optional[str] = None
    dest_airport: Optional[str] = None
    codeshare: Optional[str] = None
    stops: Optional[int] = None
    equipment: Optional[str] = None


class FlightSearchResponse(BaseModel):
    """Schema for flight route search results."""
    origin: str
    destination: str
    total_routes: int
    routes: list[RouteResponse]
    note: str = (
        "Route data sourced from OpenFlights static dataset. "
        "For live pricing and availability use Amadeus or Aviationstack API."
    )


class DeparturesRequest(BaseModel):
    """Schema for requesting all departure routes from an airport."""
    iata: str = Field(..., min_length=3, max_length=3, description="Airport IATA code")
    limit: int = Field(default=20, ge=1, le=100)


class DeparturesResponse(BaseModel):
    """Schema for all departure routes from an airport."""
    airport_iata: str
    total_routes: int
    routes: list[RouteResponse]


class ArrivalsRequest(BaseModel):
    """Schema for requesting all arrival routes to an airport."""
    iata: str = Field(..., min_length=3, max_length=3, description="Airport IATA code")
    limit: int = Field(default=20, ge=1, le=100)


class ArrivalsResponse(BaseModel):
    """Schema for all arrival routes to an airport."""
    airport_iata: str
    total_routes: int
    routes: list[RouteResponse]


# ── Airline schemas ───────────────────────────────────────────────────────────

class AirlineSearchRequest(BaseModel):
    """Schema for searching airlines by name, IATA code or country."""
    query: str = Field(..., min_length=2, description="Airline name, IATA code or country")
    limit: int = Field(default=10, ge=1, le=50)


class AirlineResponse(BaseModel):
    """Schema for a single airline result."""
    id: Optional[int] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    iata: Optional[str] = None
    icao: Optional[str] = None
    callsign: Optional[str] = None
    country: Optional[str] = None
    active: Optional[str] = None


class AirlineListResponse(BaseModel):
    """Schema for airline search results list."""
    query: str
    total: int
    airlines: list[AirlineResponse]


# ── Travel summary schema (for agent-service) ─────────────────────────────────

class TravelSummaryRequest(BaseModel):
    """Schema for natural language travel summary between two airports."""
    origin: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Origin airport IATA code"
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Destination airport IATA code"
    )


class TravelSummaryResponse(BaseModel):
    """Natural language travel summary for agent-service consumption."""
    origin: str
    destination: str
    origin_airport: Optional[AirportResponse] = None
    destination_airport: Optional[AirportResponse] = None
    total_routes: int
    airlines_serving: list[str]
    summary: str
