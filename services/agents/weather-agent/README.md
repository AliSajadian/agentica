# Weather Agent

A FastAPI microservice that provides real-time weather data and forecasts via OpenWeatherMap.
Part of the [Agentica](https://github.com/yourusername/agentica) agentic AI platform.

---

## Overview

The weather agent is a domain agent in the Agentica platform. It wraps the OpenWeatherMap API,
adds Redis caching to avoid redundant API calls, and exposes a `/summary` endpoint that returns
a natural language description of current conditions — ready to be consumed directly by
`agent-service` as tool output.

**Key design decisions:**
- Redis caches responses with a 30-minute TTL — weather doesn't change every second
- Cache keys include city, country code, and units — different unit requests are cached separately
- The `/summary` endpoint combines current + optional forecast into a single human-readable string
- Unit enum values are explicitly extracted (`.value`) before passing to the API to avoid
  sending `Units.metric` instead of `metric` to OpenWeatherMap

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| External API | OpenWeatherMap (free tier) |
| Cache | Redis |
| HTTP Client | httpx (async) |
| Validation | Pydantic v2 |
| Logging | Structlog |

---

## Prerequisites

- Docker
- Python 3.11+
- OpenWeatherMap API key (free at [openweathermap.org](https://openweathermap.org/api))
- Redis running

---

## Getting Started

### 1. Get an API key

Sign up at [openweathermap.org](https://openweathermap.org/api) and copy your API key.
Free tier allows 1,000 calls/day — sufficient for development.

### 2. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Run the service locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# set your API key in .env
cp .env.example .env
# edit OPENWEATHER_API_KEY in .env

uvicorn app.main:app --reload --port 8011
```

### 4. Run with Docker Compose

```bash
# from the agentica root
docker compose up --build weather-agent
```

Swagger UI available at `http://localhost:8011/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/weather/current` | Current weather for a city |
| POST | `/api/v1/weather/forecast` | 5-day forecast (3-hour intervals) |
| POST | `/api/v1/weather/summary` | Natural language summary for agent-service |
| GET | `/health` | Health check including OpenWeatherMap API status |

---

## Endpoint Reference

### `POST /api/v1/weather/current`

Get current weather conditions for a city.

**Request:**
```json
{
  "city": "Tehran",
  "country_code": "IR",
  "units": "metric"
}
```

**Response:**
```json
{
  "city": "Tehran",
  "country": "IR",
  "temperature": 32.5,
  "feels_like": 30.1,
  "temp_min": 28.0,
  "temp_max": 35.2,
  "humidity": 25,
  "pressure": 1012,
  "description": "clear sky",
  "icon": "01d",
  "wind_speed": 3.2,
  "wind_direction": 270,
  "visibility": 10000,
  "units": "metric",
  "cached": false
}
```

**Units:**

| Value | Temperature | Wind Speed |
|---|---|---|
| `metric` | °C | m/s |
| `imperial` | °F | mph |
| `standard` | Kelvin | m/s |

**`cached: true`** means the response was served from Redis, not the OpenWeatherMap API.

---

### `POST /api/v1/weather/forecast`

Get a 5-day weather forecast in 3-hour intervals (up to 40 data points).

**Request:**
```json
{
  "city": "Paris",
  "country_code": "FR",
  "days": 3,
  "units": "metric"
}
```

**Response:**
```json
{
  "city": "Paris",
  "country": "FR",
  "days": 3,
  "forecast": [
    {
      "datetime": "2026-06-01 12:00:00",
      "temperature": 22.3,
      "feels_like": 21.0,
      "description": "light rain",
      "icon": "10d",
      "humidity": 72,
      "wind_speed": 4.1,
      "rain_probability": 0.68
    }
  ],
  "units": "metric",
  "cached": false
}
```

`days` is capped at 5 (OpenWeatherMap free tier limit).
`rain_probability` is a value between 0.0 and 1.0.

---

### `POST /api/v1/weather/summary`

Get a natural language weather summary — designed for consumption by `agent-service`
as a tool result that can be passed directly into an LLM prompt.

**Request:**
```json
{
  "city": "Urmia",
  "country_code": "IR",
  "include_forecast": true,
  "units": "metric"
}
```

**Response:**
```json
{
  "city": "Urmia",
  "summary": "Current weather in Urmia, IR: Clear sky, temperature 28.4°C (feels like 26.1°C), humidity 30%, wind speed 2.5 m/s. 5-day forecast available with 24 data points.",
  "current": { ... },
  "forecast": { ... }
}
```

The `summary` string is ready to inject directly into an LLM system prompt or agent context.
Set `include_forecast: false` to get current conditions only (faster, fewer API calls).

---

### `GET /health`

```json
{
  "status": "ok",
  "service": "weather-agent",
  "env": "development",
  "openweather_api": "connected"
}
```

`openweather_api` is checked by making a test request to OpenWeatherMap on startup and health check.

---

## How It Works

### Request flow

```
POST /api/v1/weather/current  {city: "Tehran", units: "metric"}
  │
  ├── 1. Pydantic validates request
  ├── 2. Build Redis cache key: weather:current:Tehran:IR:metric
  ├── 3. Check Redis
  │     → cache hit  → return cached result (cached: true)
  │     → cache miss → continue
  ├── 4. Call OpenWeatherMap /data/2.5/weather
  │        params: q=Tehran,IR&units=metric&appid=...
  ├── 5. Parse response → WeatherResponse
  ├── 6. Store in Redis with TTL=1800s
  └── 7. Return response (cached: false)
```

### Cache invalidation

Weather cache is time-based only — TTL expires automatically.
There is no manual invalidation since weather data is naturally stale after 30 minutes.

```
Cache key format:
  weather:current:{city}:{country_code}:{units}
  weather:forecast:{city}:{country_code}:{units}
```

Different unit requests are cached independently — switching from `metric` to `imperial`
fetches fresh data and caches it under a separate key.

---

## Configuration

Copy `.env.example` to `.env`:

```env
APP_NAME=weather-agent
APP_ENV=development
APP_PORT=8011

OPENWEATHER_API_KEY=your-openweathermap-api-key
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5
OPENWEATHER_UNITS=metric
OPENWEATHER_LANG=en

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=2
WEATHER_CACHE_TTL=1800

LOG_LEVEL=INFO
```

### Key settings

| Variable | Default | Description |
|---|---|---|
| `OPENWEATHER_API_KEY` | — | Required — get free at openweathermap.org |
| `OPENWEATHER_UNITS` | metric | Default unit system |
| `WEATHER_CACHE_TTL` | 1800 | Cache TTL in seconds (30 minutes) |
| `REDIS_DB` | 2 | Isolated Redis DB (DB 2 reserved for weather) |

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests mock the OpenWeatherMap HTTP client and Redis cache — no API key or running Redis required.

---

## Project Structure

```
weather-agent/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                   # FastAPI app, lifespan, API reachability check
│   ├── config.py                 # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       └── weather.py        # current, forecast, summary endpoints
│   ├── core/
│   │   └── openweather.py        # Async OpenWeatherMap HTTP client
│   ├── services/
│   │   └── weather.py            # Cache strategy, response parsing, summary builder
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response schemas
│   └── utils/
│       └── logger.py             # Structlog setup
└── tests/
    ├── conftest.py
    └── test_weather.py
```

---

## Regional Note

OpenWeatherMap API is accessible from Iran. If you experience connectivity issues
with other search or data APIs in this project, OpenWeatherMap remains a reliable
choice as it does not apply regional restrictions.

---

## Part of Agentica

```
agent-service
    └── → weather-agent  ← you are here (port 8011)
              └── → OpenWeatherMap API
                        ↑
                    Redis cache (DB 0)
```

See the [main repository](https://github.com/yourusername/agentica) for the full platform.

---

## License

MIT