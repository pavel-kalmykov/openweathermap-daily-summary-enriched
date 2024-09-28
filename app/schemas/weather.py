from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas import GeocodingResult


class WeatherSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    latitude: float
    longitude: float
    timezone: str
    temp_min: float
    temp_max: float
    temp_afternoon: float
    temp_night: float
    temp_evening: float
    temp_morning: float
    temp_range: float
    cloud_cover_afternoon: float
    humidity_afternoon: float
    precipitation_total: float
    pressure_afternoon: float
    wind_speed_max: float
    wind_direction_max: float
    temp_variability_index: float
    season: str
    extreme_temperature: bool
    extreme_precipitation: bool
    extreme_wind: bool
    humidex: float
    precipitation_intensity: str


class WeatherServiceResponse(BaseModel):
    weather_data: list[WeatherSummaryResponse]
    errors: list[str | dict[str, Any]]
    geocoding_results: list[GeocodingResult]
