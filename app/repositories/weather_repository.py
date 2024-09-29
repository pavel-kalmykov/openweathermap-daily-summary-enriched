from datetime import date
from typing import Annotated, Self

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models import WeatherDailySummary


class WeatherRepository:
    """
    Repository class for managing weather data in the database.

    This class provides methods to fetch and store weather data in the database.

    Attributes:
        session (AsyncSession): The database session for executing queries.
    """

    def __init__(self: Self, session: Annotated[AsyncSession, Depends(get_db_session)]):
        self.session = session

    async def get_daily_summaries(
        self: Self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> list[WeatherDailySummary]:
        """
        Retrieve daily weather summaries for a specific location and date range.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            start_date: Start date of the range.
            end_date: End date of the range.

        Returns:
            A list of WeatherDailySummary objects matching the criteria.
        """
        query = select(WeatherDailySummary).where(
            WeatherDailySummary.latitude == latitude,
            WeatherDailySummary.longitude == longitude,
            WeatherDailySummary.date >= start_date,
            WeatherDailySummary.date <= end_date,
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def bulk_create_daily_summaries(
        self: Self, daily_summaries: list[WeatherDailySummary]
    ) -> list[WeatherDailySummary]:
        """
        Store multiple daily weather summaries in the database.

        Args:
            daily_summaries: A list of WeatherDailySummary objects to be saved.

        Returns:
            The list of stored WeatherDailySummary objects.
        """
        self.session.add_all(daily_summaries)
        await self.session.flush()
        return daily_summaries
