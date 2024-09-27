# app/services/weather_data_fetcher.py
import asyncio
from datetime import date
from typing import Any, Dict, List, Tuple

import httpx
from aiolimiter import AsyncLimiter

from app.core.config import settings

JsonType = Dict[str, Any]


class WeatherDataFetcher:
    def __init__(self, max_calls_per_minute: int | None = None):
        self.limiter = AsyncLimiter(
            max_rate=max_calls_per_minute
            or settings.openweathermap_max_calls_per_minute
        )

    async def fetch_weather_data(
        self, latitude: str, longitude: str, dates: List[date]
    ) -> Tuple[List[JsonType], List[JsonType]]:
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
    ) -> JsonType:
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
            return response.json()
