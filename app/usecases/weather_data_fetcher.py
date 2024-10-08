# app/services/weather_data_fetcher.py
import asyncio
from datetime import date
from typing import Any, Self, cast

import httpx
from aiolimiter import AsyncLimiter
from fastapi import status

from app.core.config import settings
from app.core.exceptions import WeatherDataFetcherError, get_exception_traceback
from app.core.logging import logger
from app.schemas import GeocodingResult, WeatherDailySummaryResult

JsonType = dict[str, Any]


class WeatherDataFetcher:
    """
    A class for fetching weather data from the OpenWeatherMap external API.

    This class fetches weather data for specific locations and dates,
    as well as geocoding lat/lon coordinates for location names.

    Attributes:
        limiter (AsyncLimiter): Rate limiter for API calls.
    """

    def __init__(self: Self):
        self.limiter = AsyncLimiter(settings.openweathermap_max_calls_per_minute)

    async def fetch_weather_data(
        self: Self, latitude: str, longitude: str, dates: list[date]
    ) -> tuple[list[WeatherDailySummaryResult], list[JsonType]]:
        """
        Fetch weather data for given coordinates and dates.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            dates: List of dates for which to fetch weather data.

        Returns:
            A tuple containing a list of WeatherDailySummaryResult objects and a list of errors.
        """
        logger.debug(
            f"Fetching weather data for coordinates ({latitude}, {longitude}) for {len(dates)} dates"
        )
        tasks = [self._fetch_single_day(latitude, longitude, date) for date in dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        api_results = []
        api_errors = []

        for result, day in zip(results, dates):
            if isinstance(result, Exception):
                error_msg = str(result)
                if isinstance(result, httpx.HTTPStatusError):
                    response = cast(httpx.HTTPStatusError, result).response
                    if response.status_code == status.HTTP_400_BAD_REQUEST:
                        error_msg = response.json()
                    else:
                        error_msg = "Error fetching weather daily summary from API"
                stack_trace = get_exception_traceback(result)
                logger.error(
                    f"Error fetching data for {day}: {error_msg}. Stack trace: {stack_trace}"
                )
                api_errors.append({"date": day, "message": error_msg})
            else:
                api_results.append(result)
        logger.debug(
            f"Weather data fetch for coordinates ({latitude}, {longitude}) completed. Results: {len(api_results)}, Errors: {len(api_errors)}"
        )
        return api_results, api_errors

    async def _fetch_single_day(
        self: Self, latitude: str, longitude: str, day: date
    ) -> WeatherDailySummaryResult:
        """
        Fetch weather data for a single day.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            day: The date for which to fetch weather data.

        Returns:
            WeatherDailySummaryResult object containing the weather data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "date": day.isoformat(),
            "appid": settings.api_key,
            "units": "standard",
        }
        async with self.limiter, httpx.AsyncClient() as client:
            response = await client.get(
                settings.openweathermap_day_summary_url, params=params
            )
            response.raise_for_status()
            return WeatherDailySummaryResult.model_validate_json(response.text)

    async def fetch_coordinates(
        self: Self, location_name: str
    ) -> list[GeocodingResult]:
        """
        Fetch coordinates for a given location name.

        Args:
            location_name: Name of the location to geocode.

        Returns:
            List of GeocodingResult objects containing location information.

        Raises:
            WeatherDataFetcherError: If the API request fails.
        """
        logger.debug(f"Fetching coordinates for {location_name}")
        params = {
            "q": location_name,
            "limit": settings.geocoding_results_limit,
            "appid": settings.api_key,
        }
        async with self.limiter, httpx.AsyncClient() as client:
            response = await client.get(settings.geocoding_api_url, params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                msg = "Error fetching coordinates from API"
                raise WeatherDataFetcherError(msg) from exc
            logger.debug(f"Fetching coordinates for {location_name} completed.")
            return [GeocodingResult.model_validate(item) for item in response.json()]
