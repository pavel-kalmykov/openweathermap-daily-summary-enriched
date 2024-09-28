from datetime import date, timedelta
from typing import Annotated, Any, Dict, List, Tuple

from fastapi import Depends

from app.core.config import settings
from app.models.weather import WeatherDailySummary
from app.repositories import WeatherRepository
from app.usecases import WeatherDataFetcher, WeatherDataProcessor


class WeatherService:
    MAX_DATE_RANGE = timedelta(days=settings.weather_service_max_date_range)

    def __init__(
        self,
        weather_repository: Annotated[WeatherRepository, Depends()],
        weater_data_fetcher: Annotated[WeatherDataFetcher, Depends()],
        weather_data_processor: Annotated[WeatherDataProcessor, Depends()],
    ):
        self.weather_repository = weather_repository
        self.weater_data_fetcher = weater_data_fetcher
        self.weather_data_processor = weather_data_processor

    async def get_weather_data(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> Tuple[List[WeatherDailySummary], List[Dict[str, Any]]]:
        if end_date - start_date > self.MAX_DATE_RANGE:
            raise ValueError(
                f"Date range exceeds maximum allowed ({self.MAX_DATE_RANGE.days} days)"
            )

        # Query the database for existing data
        existing_summaries = await self.weather_repository.get_daily_summaries(
            latitude, longitude, start_date, end_date
        )

        # Identify missing dates
        existing_dates = set(summary.date for summary in existing_summaries)
        all_dates = set(
            date.fromordinal(d)
            for d in range(start_date.toordinal(), end_date.toordinal() + 1)
        )
        missing_dates = sorted(list(all_dates - existing_dates))

        # Fetch missing data from API
        api_results, api_errors = await self.weater_data_fetcher.fetch_weather_data(
            latitude, longitude, missing_dates
        )

        # Process and save new data
        if api_results:
            processed_data = self.weather_data_processor.process_data(api_results)
            new_summaries = []
            # Potential memory hog, but since we do not allow a wide range of days, it is fine.
            # Alternative (not verified): processed_data.write_database(WeatherDailySummary.__tablename__, self.weather_repository.session, if_table_exists="append").
            # However, this way we would "skip" the ORM (for the better or the worse)
            for row in processed_data.to_dicts():
                summary = WeatherDailySummary(**row)
                new_summaries.append(summary)
            saved_summaries = await self.weather_repository.bulk_create_daily_summaries(
                new_summaries
            )
            existing_summaries.extend(saved_summaries)

        # Combine all data and return
        all_summaries = sorted(existing_summaries, key=lambda x: x.date)
        return all_summaries, api_errors
