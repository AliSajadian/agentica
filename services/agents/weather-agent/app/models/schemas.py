from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Units(str, Enum):
    """Temperature unit options."""
    metric = "metric"
    imperial = "imperial"
    standard = "standard"


# ── Current weather ───────────────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    """Schema for current weather request."""
    city: str = Field(..., min_length=1, description="City name")
    country_code: Optional[str] = Field(None, description="ISO country code e.g. US, GB, IR")
    units: Units = Field(default=Units.metric)


class WeatherCondition(BaseModel):
    """Describes the weather condition."""
    id: int
    main: str
    description: str
    icon: str


class WeatherMain(BaseModel):
    """Main weather metrics."""
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    pressure: int


class WindInfo(BaseModel):
    """Wind speed and direction."""
    speed: float
    direction: Optional[int] = None


class WeatherResponse(BaseModel):
    """Full current weather response."""
    city: str
    country: str
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    pressure: int
    description: str
    icon: str
    wind_speed: float
    wind_direction: Optional[int] = None
    visibility: Optional[int] = None
    units: str
    cached: bool = False


# ── Forecast ──────────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    """Schema for weather forecast request."""
    city: str = Field(..., min_length=1)
    country_code: Optional[str] = None
    days: int = Field(default=5, ge=1, le=5)
    units: Units = Field(default=Units.metric)


class ForecastItem(BaseModel):
    """Single forecast time slot."""
    datetime: str
    temperature: float
    feels_like: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    rain_probability: float = 0.0


class ForecastResponse(BaseModel):
    """Full forecast response with multiple time slots."""
    city: str
    country: str
    days: int
    forecast: list[ForecastItem]
    units: str
    cached: bool = False


# ── Summary (for agent-service) ───────────────────────────────────────────────

class WeatherSummaryRequest(BaseModel):
    """Schema for natural language weather summary request."""
    city: str = Field(..., min_length=1)
    country_code: Optional[str] = None
    include_forecast: bool = False
    units: Units = Field(default=Units.metric)


class WeatherSummaryResponse(BaseModel):
    """Natural language weather summary for agent consumption."""
    city: str
    summary: str
    current: WeatherResponse
    forecast: Optional[ForecastResponse] = None
