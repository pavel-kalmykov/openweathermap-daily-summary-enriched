from pydantic import BaseModel


class CloudCover(BaseModel):
    afternoon: float


class Humidity(BaseModel):
    afternoon: float


class Precipitation(BaseModel):
    total: float


class Temperature(BaseModel):
    min: float
    max: float
    afternoon: float
    night: float
    evening: float
    morning: float


class Pressure(BaseModel):
    afternoon: float


class Max(BaseModel):
    speed: float
    direction: float


class Wind(BaseModel):
    max: Max


class WeatherDailySummaryResult(BaseModel):
    lat: float
    lon: float
    tz: str
    date: str
    units: str
    cloud_cover: CloudCover
    humidity: Humidity
    precipitation: Precipitation
    temperature: Temperature
    pressure: Pressure
    wind: Wind


class GeocodingResult(BaseModel):
    name: str
    local_names: dict[str, str] | None = None
    lat: float
    lon: float
    country: str | None = None
    state: str | None = None
