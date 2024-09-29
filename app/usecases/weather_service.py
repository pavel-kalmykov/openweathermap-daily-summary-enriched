from datetime import date, timedelta
from typing import Annotated, Self

from fastapi import Depends

from app.core.config import settings
from app.core.exceptions import WeatherDataFetcherError, WeatherServiceInputError
from app.core.logging import logger
from app.models.weather import WeatherDailySummary
from app.repositories import WeatherRepository
from app.schemas import WeatherServiceResponse, WeatherSummaryResponse
from app.usecases import WeatherDataFetcher, WeatherDataProcessor


class WeatherService:
    """
    Service class for managing weather data operations.

    This class provides methods for retrieving and processing weather data
    for specific locations and date ranges.

    Attributes:
        MAX_DATE_RANGE (timedelta): Maximum allowed date range for weather data retrieval.
        weather_repository (WeatherRepository): Repository for weather data storage and retrieval.
        weater_data_fetcher (WeatherDataFetcher): Service for fetching weather data from external API.
        weather_data_processor (WeatherDataProcessor): Service for processing raw weather data.
    """

    MAX_DATE_RANGE = timedelta(days=settings.weather_service_max_date_range)

    def __init__(
        self: Self,
        weather_repository: Annotated[WeatherRepository, Depends()],
        weater_data_fetcher: Annotated[WeatherDataFetcher, Depends()],
        weather_data_processor: Annotated[WeatherDataProcessor, Depends()],
    ):
        self.weather_repository = weather_repository
        self.weater_data_fetcher = weater_data_fetcher
        self.weather_data_processor = weather_data_processor

    def _validate_date_range(self: Self, start_date: date, end_date: date) -> None:
        """
        Validate the given date range.

        Args:
            start_date: The start date of the range.
            end_date: The end date of the range.

        Raises:
            WeatherServiceInputError: If the date range exceeds the maximum allowed range.
        """
        if end_date - start_date > self.MAX_DATE_RANGE:
            msg = (
                f"Date range exceeds maximum allowed ({self.MAX_DATE_RANGE.days} days)"
            )
            raise WeatherServiceInputError(msg)

    async def get_weather_data_by_name(
        self: Self, location_name: str, start_date: date, end_date: date
    ) -> WeatherServiceResponse:
        """
        Get weather data for a location by its name.

        Args:
            location_name: Name of the location.
            start_date: Start date for the weather data.
            end_date: End date for the weather data.

        Returns:
            WeatherServiceResponse containing the weather data, any errors, and geocoding results.
        """
        logger.debug(
            f"Getting weather data for location: {location_name} from {start_date} to {end_date}"
        )
        self._validate_date_range(start_date, end_date)

        try:
            geocoding_results = await self.weater_data_fetcher.fetch_coordinates(
                location_name
            )
        except WeatherDataFetcherError:
            geocoding_results = []
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
        logger.debug(
            f"Weather data retrieved for {location_name} from {start_date} to {end_date}. "
            f"Results: {len(weather_response.weather_data)}, "
            f"Errors: {len(weather_response.errors)}"
        )
        return weather_response

    async def get_weather_data(
        self: Self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> WeatherServiceResponse:
        """
        Get weather data for a location by its coordinates.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            start_date: Start date for the weather data.
            end_date: End date for the weather data.

        Returns:
            WeatherServiceResponse containing the weather data and any errors.
        """
        logger.debug(
            f"Getting weather data for coordinates ({latitude}, {longitude}) from {start_date} to {end_date}"
        )
        self._validate_date_range(start_date, end_date)

        # Query the database for existing data
        existing_summaries = await self.weather_repository.get_daily_summaries(
            latitude, longitude, start_date, end_date
        )

        # Identify missing dates
        existing_dates = {summary.date for summary in existing_summaries}
        all_dates = {
            date.fromordinal(d)
            for d in range(start_date.toordinal(), end_date.toordinal() + 1)
        }
        missing_dates = sorted(all_dates - existing_dates)

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
            logger.info(
                f"Saved {len(new_summaries)} daily summaries for coordinates ({latitude}, {longitude}) from {start_date} to {end_date}"
            )
            existing_summaries.extend(saved_summaries)

        # Combine all data and return
        existing_summaries.sort(key=lambda x: x.date)
        logger.debug(
            f"Weather data for coordinates ({latitude}, {longitude}) from {start_date} to {end_date} retrieved. "
            f"Results: {len(existing_summaries)}, "
            f"Errors: {len(api_errors)}"
        )
        return WeatherServiceResponse(
            weather_data=[
                WeatherSummaryResponse.model_validate(data)
                for data in existing_summaries
            ],
            errors=api_errors,
            geocoding_results=[],
        )
