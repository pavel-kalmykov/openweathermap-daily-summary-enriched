from datetime import date, timedelta
from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.core.exceptions import WeatherDataFetcherError, WeatherServiceInputError
from app.models.weather import WeatherDailySummary
from app.repositories import WeatherRepository
from app.schemas import WeatherServiceResponse, WeatherSummaryResponse
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

    def _validate_date_range(self, start_date: date, end_date: date) -> None:
        if end_date - start_date > self.MAX_DATE_RANGE:
            raise WeatherServiceInputError(
                f"Date range exceeds maximum allowed ({self.MAX_DATE_RANGE.days} days)"
            )

    async def get_weather_data_by_name(
        self, location_name: str, start_date: date, end_date: date
    ) -> WeatherServiceResponse:
        self._validate_date_range(start_date, end_date)

        geocoding_results = []
        try:
            geocoding_results = await self.weater_data_fetcher.fetch_coordinates(
                location_name
            )
        except WeatherDataFetcherError as exc:
            raise WeatherServiceInputError(exc) from exc
        if not geocoding_results:
            return WeatherServiceResponse(
                weather_data=[],
                errors=[
                    {
                        "message": f"Could not find coordinates for location: {location_name}"
                    }
                ],
                geocoding_results=[],
            )

        if len(geocoding_results) > 1:
            return WeatherServiceResponse(
                weather_data=[],
                errors=[
                    {
                        "message": "Multiple locations found. Please specify coordinates manually."
                    }
                ],
                geocoding_results=geocoding_results,
            )

        latitude, longitude = geocoding_results[0].lat, geocoding_results[0].lon
        weather_response = await self.get_weather_data(
            latitude, longitude, start_date, end_date
        )
        weather_response.geocoding_results = geocoding_results
        return weather_response

    async def get_weather_data(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> WeatherServiceResponse:
        self._validate_date_range(start_date, end_date)

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
            for processed_row in processed_data.to_dicts():
                summary = WeatherDailySummary(**processed_row)
                new_summaries.append(summary)
            saved_summaries = await self.weather_repository.bulk_create_daily_summaries(
                new_summaries
            )
            existing_summaries.extend(saved_summaries)

        # Combine all data and return
        existing_summaries.sort(key=lambda x: x.date)
        return WeatherServiceResponse(
            weather_data=[
                WeatherSummaryResponse.model_validate(data)
                for data in existing_summaries
            ],
            errors=api_errors,
            geocoding_results=[],
        )
