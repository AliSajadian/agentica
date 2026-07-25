# Travel Agent

A FastAPI microservice providing flight routes, airport and airline data using the
[OpenFlights](https://openflights.org/data.html) static dataset.
Part of the [Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The travel agent gives the Agentica platform access to real-world aviation data —
airports, airlines, and flight routes — without requiring any external API key or
internet connection at runtime. All data is loaded from the OpenFlights static dataset
into memory at startup and queried using pandas for fast in-process lookups.

Results are cached in Redis to avoid redundant dataset scans on repeated queries.

**Dataset coverage:**
- 10,000+ airports worldwide with IATA codes, coordinates and timezone info
- 67,000+ flight routes between airports
- 6,000+ active airlines with IATA/ICAO codes and country info

> **Note:** Data is sourced from the OpenFlights static dataset and reflects
> historical route information. For live pricing, seat availability and real-time
> schedules, swap `core/openflights.py` for an Amadeus or Aviationstack client
> when API access becomes available.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Data Source | OpenFlights static dataset (.dat files) |
| Data Processing | pandas |
| Cache | Redis |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- Redis running

---

## Getting Started

### 1. Download the OpenFlights dataset

```bash
mkdir -p data

wget -O data/airports.dat \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat

wget -O data/routes.dat \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat

wget -O data/airlines.dat \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
```

### 2. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Run the service locally

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8010
```

### 4. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build travel-agent
```

Swagger UI available at `http://localhost:8010/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/airports/search` | Search airports by name, city, IATA or country |
| GET | `/api/v1/airports/iata/{iata}` | Get airport by IATA code |
| GET | `/api/v1/airports/country/{country}` | Get all airports in a country |
| GET | `/api/v1/airports/city/{city}` | Get all airports in a city |
| POST | `/api/v1/airlines/search` | Search airlines by name, IATA or country |
| GET | `/api/v1/airlines/iata/{iata}` | Get airline by IATA code |
| GET | `/api/v1/airlines/country/{country}` | Get all airlines from a country |
| POST | `/api/v1/flights/search` | Search direct routes between two airports |
| POST | `/api/v1/flights/departures` | Get all departures from an airport |
| POST | `/api/v1/flights/arrivals` | Get all arrivals at an airport |
| POST | `/api/v1/flights/summary` | Natural language travel summary for agent-service |
| GET | `/health` | Health check including dataset load status |
| GET | `/ready` | Readiness probe for Kubernetes |

---

## Endpoint Reference

### `POST /api/v1/airports/search`

Search airports by name, city, IATA code or country.
Tries exact IATA match first, then falls back to partial name/city search.

**Request:**
```json
{
  "query": "Tehran",
  "limit": 10
}
```

**Response:**
```json
{
  "query": "Tehran",
  "total": 2,
  "airports": [
    {
      "id": 1,
      "name": "Imam Khomeini International Airport",
      "city": "Tehran",
      "country": "Iran",
      "iata": "IKA",
      "icao": "OIIE",
      "latitude": 35.416,
      "longitude": 51.152,
      "altitude": 3305.0,
      "timezone": 3.5
    }
  ]
}
```

---

### `GET /api/v1/airports/iata/{iata}`

Get a single airport by its 3-letter IATA code. Returns `404` if not found.

```bash
GET /api/v1/airports/iata/LHR
GET /api/v1/airports/iata/JFK
GET /api/v1/airports/iata/IKA
```

---

### `POST /api/v1/flights/search`

Search all direct routes between two airports by IATA code.
Returns list of airlines and aircraft equipment serving the route.

**Request:**
```json
{
  "origin": "IKA",
  "destination": "IST",
  "limit": 20
}
```

**Response:**
```json
{
  "origin": "IKA",
  "destination": "IST",
  "total_routes": 3,
  "routes": [
    {
      "airline": "TK",
      "airline_id": "4951",
      "source_airport": "IKA",
      "dest_airport": "IST",
      "codeshare": null,
      "stops": 0,
      "equipment": "738"
    }
  ],
  "note": "Route data sourced from OpenFlights static dataset. For live pricing and availability use Amadeus or Aviationstack API."
}
```

---

### `POST /api/v1/flights/departures`

Get all routes departing from a given airport.

**Request:**
```json
{
  "iata": "IKA",
  "limit": 50
}
```

---

### `POST /api/v1/flights/arrivals`

Get all routes arriving at a given airport.

**Request:**
```json
{
  "iata": "DXB",
  "limit": 50
}
```

---

### `POST /api/v1/flights/summary`

Get natural language travel summary for agent-service.
Combines airport info and route availability into a human-readable string
ready to inject into an LLM prompt.

**Request:**
```json
{
  "origin": "IKA",
  "destination": "LHR"
}
```

**Response:**
```json
{
  "origin": "IKA",
  "destination": "LHR",
  "origin_airport": { "name": "Imam Khomeini International Airport", "city": "Tehran", ... },
  "destination_airport": { "name": "Heathrow Airport", "city": "London", ... },
  "total_routes": 2,
  "airlines_serving": ["IR", "BA"],
  "summary": "Route from Imam Khomeini International Airport, Tehran, Iran (IKA) to Heathrow Airport, London, United Kingdom (LHR): 2 direct route(s) found, operated by airlines: IR, BA."
}
```

---

### `POST /api/v1/airlines/search`

Search active airlines by name, IATA code or country.

**Request:**
```json
{
  "query": "Iran",
  "limit": 10
}
```

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "travel-agent",
  "env": "development",
  "data_loaded": true,
  "airports": 10234,
  "routes": 67663,
  "airlines": 3216
}
```

---

### `GET /ready`

Kubernetes readiness probe — returns `200` only when all datasets are fully loaded.
Returns `503` if datasets are still loading.

---

## How It Works

### Data loading

```
FastAPI lifespan startup
    → pandas reads airports.dat  → filter valid IATA + type=airport
    → pandas reads routes.dat    → filter non-null source/dest
    → pandas reads airlines.dat  → filter active=Y
    → all 3 DataFrames held in memory for the lifetime of the process
```

### Request flow

```
API request
    → check Redis cache (key: travel:{type}:{params})
        → cache hit  → return instantly
        → cache miss → pandas DataFrame query (milliseconds)
                     → store result in Redis with TTL
                     → return result
```

### Why Redis matters

Without Redis, every request scans the pandas DataFrames. With Redis, repeated
queries (same airport, same route) return from cache in under 1ms.
If Redis is unreachable, the service falls back gracefully to direct DataFrame queries.

---

## Configuration

Copy `.env.example` to `.env`:

```env
APP_NAME=travel-agent
APP_ENV=development
APP_PORT=8010
DEBUG=true

AIRPORTS_DATA_PATH=data/airports.dat
ROUTES_DATA_PATH=data/routes.dat
AIRLINES_DATA_PATH=data/airlines.dat

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=4
TRAVEL_CACHE_TTL=3600

LOG_LEVEL=INFO
```

| Variable | Default | Description |
|---|---|---|
| `AIRPORTS_DATA_PATH` | data/airports.dat | Path to airports dataset |
| `ROUTES_DATA_PATH` | data/routes.dat | Path to routes dataset |
| `AIRLINES_DATA_PATH` | data/airlines.dat | Path to airlines dataset |
| `TRAVEL_CACHE_TTL` | 3600 | Redis cache TTL in seconds (1 hour) |
| `REDIS_DB` | 4 | Redis database index (isolated per service) |

---

## Project Structure

```
travel-agent/
├── Dockerfile
├── requirements.txt
├── .env.example
├── data/
│   ├── airports.dat           # OpenFlights airport dataset (10,000+ airports)
│   ├── routes.dat             # OpenFlights routes dataset (67,000+ routes)
│   └── airlines.dat           # OpenFlights airlines dataset (6,000+ airlines)
├── app/
│   ├── main.py                # FastAPI app, lifespan, dataset loading
│   ├── config.py              # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       ├── airports.py    # Airport search endpoints
│   │       ├── airlines.py    # Airline search endpoints
│   │       └── flights.py     # Flight route endpoints
│   ├── core/
│   │   └── openflights.py     # Pandas data loader and query engine
│   ├── services/
│   │   ├── airport.py         # Airport business logic + Redis cache
│   │   ├── airline.py         # Airline business logic + Redis cache
│   │   └── flight.py          # Flight business logic + Redis cache
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response schemas
│   └── utils/
│       └── logger.py          # Structlog setup
└── tests/
    ├── conftest.py
    └── test_flights.py
```

---

## Switching to a Live API

The service is designed for easy provider swap. Replace `app/core/openflights.py`
with a live API client:

### Amadeus
```python
# pip install amadeus
from amadeus import Client
client = Client(client_id=settings.AMADEUS_KEY, client_secret=settings.AMADEUS_SECRET)
response = client.shopping.flight_offers_search.get(
    originLocationCode="IKA",
    destinationLocationCode="LHR",
    departureDate="2026-08-01",
    adults=1
)
```

### Aviationstack (500 free calls/month)
```python
# no extra package needed — plain HTTP
params = {
    "access_key": settings.AVIATIONSTACK_KEY,
    "dep_iata": "IKA",
    "arr_iata": "LHR"
}
response = await httpx.get("http://api.aviationstack.com/v1/flights", params=params)
```

The service layer (`services/airport.py`, `services/flight.py`, `services/airline.py`)
and all API endpoints remain unchanged — only the data source swaps.

---

## Part of Agentica

```
gateway-service
    → agent-service
        → travel-agent  ← you are here
            → OpenFlights dataset (local)
            → Redis (cache)
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT