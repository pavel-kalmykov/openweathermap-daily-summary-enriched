from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas import WeatherServiceResponse
from app.usecases import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/enriched-day-summary",
    response_model=WeatherServiceResponse,
    summary="Get enriched weather data for a location",
    description="""
Retrieve enriched weather data for a specific location and date range.

You can specify the location either by latitude and longitude coordinates or by location name.
The date range is required and should not exceed 31 days.

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
                        "detail": "Provide either latitude and longitude OR location, not both"
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
    if (latitude is not None and longitude is not None) and location is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either latitude and longitude OR location, not both",
        )

    if latitude is not None and longitude is not None:
        return await weather_service.get_weather_data(
            latitude, longitude, start_date, end_date
        )
    elif location is not None:
        return await weather_service.get_weather_data_by_name(
            location, start_date, end_date
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either latitude and longitude OR location",
        )
