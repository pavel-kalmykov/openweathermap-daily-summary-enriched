from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models import WeatherDailySummary


class WeatherRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_db_session)]):
        self.session = session

    async def get_daily_summaries(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> list[WeatherDailySummary]:
        query = select(WeatherDailySummary).where(
            WeatherDailySummary.latitude == latitude,
            WeatherDailySummary.longitude == longitude,
            WeatherDailySummary.date >= start_date,
            WeatherDailySummary.date <= end_date,
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def bulk_create_daily_summaries(
        self, daily_summaries: list[WeatherDailySummary]
    ) -> list[WeatherDailySummary]:
        self.session.add_all(daily_summaries)
        await self.session.flush()
        return daily_summaries
