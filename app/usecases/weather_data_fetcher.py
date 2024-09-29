# app/services/weather_data_fetcher.py
import asyncio
from datetime import date
from typing import Any, cast

import httpx
from aiolimiter import AsyncLimiter
from fastapi import status

from app.core.config import settings
from app.core.exceptions import WeatherDataFetcherError
from app.schemas import GeocodingResult, WeatherDailySummaryResult

JsonType = dict[str, Any]


class WeatherDataFetcher:
    def __init__(self):
        self.limiter = AsyncLimiter(settings.openweathermap_max_calls_per_minute)

    async def fetch_weather_data(
        self, latitude: str, longitude: str, dates: list[date]
    ) -> tuple[list[WeatherDailySummaryResult], list[JsonType]]:
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
                api_errors.append({"date": day, "message": error_msg})
            else:
                api_results.append(result)

        return api_results, api_errors

    async def _fetch_single_day(
        self, latitude: str, longitude: str, day: date
    ) -> WeatherDailySummaryResult:
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

    async def fetch_coordinates(self, location_name: str) -> list[GeocodingResult]:
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
                raise WeatherDataFetcherError(
                    "Error fetching coordinates from API"
                ) from exc
            return [GeocodingResult.model_validate(item) for item in response.json()]
