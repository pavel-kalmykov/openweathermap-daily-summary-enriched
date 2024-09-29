from typing import Self

from sqlalchemy import Boolean, Column, Date, Float, Integer, String

from app.core.database import Base


class WeatherDailySummary(Base):
    __tablename__ = "weather_daily_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    date = Column(Date, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    timezone = Column(String, nullable=False)

    # Temperature data
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    temp_afternoon = Column(Float, nullable=False)
    temp_night = Column(Float, nullable=False)
    temp_evening = Column(Float, nullable=False)
    temp_morning = Column(Float, nullable=False)
    temp_range = Column(Float, nullable=False)

    # Other weather data
    cloud_cover_afternoon = Column(Float, nullable=False)
    humidity_afternoon = Column(Float, nullable=False)
    precipitation_total = Column(Float, nullable=False)
    pressure_afternoon = Column(Float, nullable=False)
    wind_speed_max = Column(Float, nullable=False)
    wind_direction_max = Column(Float, nullable=False)

    # Derived metrics
    temp_variability_index = Column(Float, nullable=False)
    season = Column(String, nullable=False)
    extreme_temperature = Column(Boolean, nullable=False)
    extreme_precipitation = Column(Boolean, nullable=False)
    extreme_wind = Column(Boolean, nullable=False)
    humidex = Column(Float, nullable=False)
    precipitation_intensity = Column(String, nullable=False)
    rolling_mean_temp = Column(Float, nullable=True)
    wind_chill = Column(Float, nullable=True)
    heat_index = Column(Float, nullable=True)

    def __repr__(self: Self) -> str:
        return f"<WeatherDailySummary(date='{self.date}', lat={self.latitude}, lon={self.longitude})>"
