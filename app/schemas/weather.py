from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import GeocodingResult


class WeatherSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: Annotated[date, Field(description="The date of the weather summary")]
    latitude: Annotated[float, Field(description="Latitude of the location")]
    longitude: Annotated[float, Field(description="Longitude of the location")]
    timezone: Annotated[str, Field(description="Timezone of the location")]
    temp_min: Annotated[
        float, Field(description="Minimum temperature of the day in Kelvin")
    ]
    temp_max: Annotated[
        float, Field(description="Maximum temperature of the day in Kelvin")
    ]
    temp_afternoon: Annotated[
        float, Field(description="Afternoon temperature in Kelvin")
    ]
    temp_night: Annotated[float, Field(description="Night temperature in Kelvin")]
    temp_evening: Annotated[float, Field(description="Evening temperature in Kelvin")]
    temp_morning: Annotated[float, Field(description="Morning temperature in Kelvin")]
    temp_range: Annotated[
        float, Field(description="Temperature range (max - min) in Kelvin")
    ]
    cloud_cover_afternoon: Annotated[
        float, Field(description="Afternoon cloud cover percentage")
    ]
    humidity_afternoon: Annotated[
        float, Field(description="Afternoon humidity percentage")
    ]
    precipitation_total: Annotated[
        float, Field(description="Total precipitation in mm")
    ]
    pressure_afternoon: Annotated[
        float, Field(description="Afternoon atmospheric pressure in hPa")
    ]
    wind_speed_max: Annotated[float, Field(description="Maximum wind speed in m/s")]
    wind_direction_max: Annotated[
        float, Field(description="Direction of maximum wind in degrees")
    ]
    temp_variability_index: Annotated[
        float, Field(description="Temperature variability index")
    ]
    season: Annotated[
        str, Field(description="Seasonal classification based on temperature")
    ]
    extreme_temperature: Annotated[
        bool, Field(description="Flag for extreme temperature conditions")
    ]
    extreme_precipitation: Annotated[
        bool, Field(description="Flag for extreme precipitation conditions")
    ]
    extreme_wind: Annotated[bool, Field(description="Flag for extreme wind conditions")]
    humidex: Annotated[
        float, Field(description="Humidex value (felt air temperature) in Kelvin")
    ]
    precipitation_intensity: Annotated[
        str, Field(description="Qualitative description of precipitation intensity")
    ]


class WeatherServiceResponse(BaseModel):
    weather_data: Annotated[
        list[WeatherSummaryResponse],
        Field(description="List of daily weather summaries"),
    ]
    errors: Annotated[
        list[str | dict[str, Any]],
        Field(
            default=[],
            description="List of errors encountered during data retrieval or processing",
        ),
    ]
    geocoding_results: Annotated[
        list[GeocodingResult],
        Field(
            default=[],
            description="List of geocoding results if a location name was provided",
        ),
    ]
