# tests/test_weather_processor.py

from datetime import date

import polars as pl
import pytest
from app.schemas import WeatherDailySummaryResult
from app.usecases import WeatherDataProcessor


@pytest.fixture
def sample_data() -> list[WeatherDailySummaryResult]:
    return [
        WeatherDailySummaryResult.model_validate(
            {
                "lat": 33,
                "lon": 35,
                "tz": "+02:00",
                "date": "2020-07-15",
                "units": "standard",
                "cloud_cover": {"afternoon": 10},
                "humidity": {"afternoon": 70},
                "precipitation": {"total": 55},
                "temperature": {
                    "min": 293.15,  # 20°C
                    "max": 308.15,  # 35°C
                    "afternoon": 306.15,  # 33°C
                    "night": 295.15,
                    "evening": 303.15,
                    "morning": 294.15,
                },
                "pressure": {"afternoon": 1010},
                "wind": {"max": {"speed": 22, "direction": 180}},
            }
        )
    ]


def test_weather_data_processor(sample_data: list[WeatherDailySummaryResult]):
    processor = WeatherDataProcessor()
    result = processor.process_data(sample_data)

    # Check if the result is a Polars DataFrame
    assert isinstance(result, pl.DataFrame)

    # Check if we have the correct number of rows
    assert len(result) == 1

    # Check if all expected columns are present
    expected_columns = [
        "latitude",
        "longitude",
        "timezone",
        "date",
        "cloud_cover_afternoon",
        "humidity_afternoon",
        "precipitation_total",
        "temp_min",
        "temp_max",
        "temp_afternoon",
        "temp_night",
        "temp_evening",
        "temp_morning",
        "pressure_afternoon",
        "wind_speed_max",
        "wind_direction_max",
        "temp_range",
        "temp_variability_index",
        "season",
        "extreme_temperature",
        "extreme_precipitation",
        "extreme_wind",
        "humidex",
        "precipitation_intensity",
        "wind_chill",
        "heat_index",
    ]
    assert all(col in result.columns for col in expected_columns)

    # Extract the single row for easier assertions
    row = result.row(0, named=True)

    # Check original data is preserved
    assert row["latitude"] == 33
    assert row["longitude"] == 35
    assert row["date"] == date(2020, 7, 15)
    assert row["cloud_cover_afternoon"] == pytest.approx(10, rel=1e-2)
    assert row["humidity_afternoon"] == pytest.approx(70, rel=1e-2)
    assert row["precipitation_total"] == pytest.approx(55, rel=1e-2)
    assert row["temp_min"] == pytest.approx(293.15, rel=1e-2)
    assert row["temp_max"] == pytest.approx(308.15, rel=1e-2)
    assert row["temp_afternoon"] == pytest.approx(306.15, rel=1e-2)
    assert row["pressure_afternoon"] == pytest.approx(1010, rel=1e-2)
    assert row["wind_speed_max"] == pytest.approx(22, rel=1e-2)
    assert row["wind_direction_max"] == pytest.approx(180, rel=1e-2)

    # Check derived values
    assert row["temp_range"] == pytest.approx(15, rel=1e-2)
    assert row["temp_variability_index"] == pytest.approx(0.0487, rel=1e-2)
    assert row["season"] == "Summer"
    assert row["extreme_temperature"] is True
    assert row["extreme_precipitation"] is True
    assert row["extreme_wind"] is True
    assert row["precipitation_intensity"] == "Heavy"

    # Check calculated indices
    assert row["humidex"] == pytest.approx(320.15, rel=1e-2)
    assert row["wind_chill"] is None  # Should be None for warm temperatures
    assert row["heat_index"] == pytest.approx(316.65, rel=1e-2)
