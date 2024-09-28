# app/services/weather_data_fetcher.py
import asyncio
from datetime import date
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from app.core.config import settings
from app.schemas import GeocodingResult, WeatherDailySummaryResult

JsonType = dict[str, Any]


class WeatherDataFetcher:
    def __init__(self, max_calls_per_minute: int | None = None):
        self.limiter = AsyncLimiter(
            max_rate=max_calls_per_minute
            or settings.openweathermap_max_calls_per_minute
        )

    async def fetch_weather_data(
        self, latitude: str, longitude: str, dates: list[date]
    ) -> tuple[list[WeatherDailySummaryResult], list[JsonType]]:
        tasks = [self._fetch_single_day(latitude, longitude, date) for date in dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        api_results = []
        api_errors = []

        for result, day in zip(results, dates):
            if isinstance(result, Exception):
                error_msg = (
                    result.response.json()
                    if isinstance(result, httpx.HTTPStatusError)
                    else str(result)
                )
                api_errors.append({"date": day, "error": error_msg})
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
            response.raise_for_status()
            return [GeocodingResult.model_validate(item) for item in response.json()]
