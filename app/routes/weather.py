from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.config import settings
from app.core.exceptions import WeatherServiceInputError
from app.schemas import WeatherServiceResponse
from app.usecases import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/enriched-day-summary",
    response_model=WeatherServiceResponse,
    summary="Get enriched weather data for a location",
    description=f"""
Retrieve enriched weather data for a specific location and date range.

You can specify the location either by latitude and longitude coordinates or by location name.
The date range is required and should not exceed {settings.weather_service_max_date_range} days. Opposed ranges will count as empty ranges.

The response includes daily weather summaries with various metrics and derived indices.
    """,
    responses={
        200: {
            "description": "Successful response with weather data",
            "content": {
                "application/json": {
                    "example": {
                        "weather_data": [
                            {
                                "date": "2024-09-27",
                                "latitude": 38.2653,
                                "longitude": -0.6988,
                                "timezone": "+02:00",
                                "temp_min": 296.38,
                                "temp_max": 302.46,
                                "temp_afternoon": 300.86,
                                "temp_night": 299.57,
                                "temp_evening": 299.95,
                                "temp_morning": 297.28,
                                "temp_range": 6.08,
                                "cloud_cover_afternoon": 0.0,
                                "humidity_afternoon": 50.0,
                                "precipitation_total": 0.0,
                                "pressure_afternoon": 1014.0,
                                "wind_speed_max": 8.23,
                                "wind_direction_max": 310.0,
                                "temp_variability_index": 0.02,
                                "season": "Summer",
                                "extreme_temperature": False,
                                "extreme_precipitation": False,
                                "extreme_wind": False,
                                "humidex": 305.86,
                                "precipitation_intensity": "None",
                            }
                        ],
                        "errors": [],
                        "geocoding_results": [],
                    }
                }
            },
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "errors": [
                            {
                                "message": "Provide either latitude and longitude OR location, not both"
                            }
                        ]
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "start_date"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def get_weather(
    response: Response,
    start_date: Annotated[
        date, Query(..., description="Start date for weather data (YYYY-MM-DD)")
    ],
    end_date: Annotated[
        date, Query(..., description="End date for weather data (YYYY-MM-DD)")
    ],
    weather_service: Annotated[WeatherService, Depends()],
    latitude: Annotated[
        float | None, Query(description="Latitude of the location")
    ] = None,
    longitude: Annotated[
        float | None, Query(description="Longitude of the location")
    ] = None,
    location: Annotated[str | None, Query(description="Name of the location")] = None,
) -> WeatherServiceResponse:
    if all(param is not None for param in (latitude, longitude, location)):
        msg = "Provide either latitude and longitude OR location, not both"
        raise WeatherServiceInputError(msg)
    if all(param is None for param in (latitude, longitude, location)):
        msg = "Provide either latitude and longitude OR location"
        raise WeatherServiceInputError(msg)

    enriched_weather_data = await (
        weather_service.get_weather_data_by_name(location, start_date, end_date)
        if location is not None
        else weather_service.get_weather_data(latitude, longitude, start_date, end_date)
    )
    if enriched_weather_data.errors:
        response.status_code = status.HTTP_206_PARTIAL_CONTENT
    return enriched_weather_data
