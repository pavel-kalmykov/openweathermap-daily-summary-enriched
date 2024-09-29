import datetime

import pytest
from app.schemas import GeocodingResult, WeatherDailySummaryResult
from app.usecases.weather_data_fetcher import WeatherDataFetcher


@pytest.mark.asyncio()
async def test_weather_data_fetcher():
    fetcher = WeatherDataFetcher()

    # No mocking becase we expect past values not to change
    api_results, api_errors = await fetcher.fetch_weather_data(
        latitude="38.2653307",
        longitude="-0.6988391",
        dates=[
            datetime.date(2024, 9, 27),
            datetime.date(2024, 9, 26),
        ],  # OK not to have them sorted
    )

    assert not api_errors
    expected_results = [
        WeatherDailySummaryResult.model_validate(
            {
                "lat": 38.2653307,
                "lon": -0.6988391,
                "tz": "+02:00",
                "date": "2024-09-27",
                "units": "standard",
                "cloud_cover": {"afternoon": 0.0},
                "humidity": {"afternoon": 50.0},
                "precipitation": {"total": 0.0},
                "temperature": {
                    "min": 296.38,
                    "max": 302.46,
                    "afternoon": 300.86,
                    "night": 299.57,
                    "evening": 299.95,
                    "morning": 297.28,
                },
                "pressure": {"afternoon": 1014.0},
                "wind": {"max": {"speed": 8.23, "direction": 310.0}},
            }
        ),
        WeatherDailySummaryResult.model_validate(
            {
                "lat": 38.2653307,
                "lon": -0.6988391,
                "tz": "+02:00",
                "date": "2024-09-26",
                "units": "standard",
                "cloud_cover": {"afternoon": 0.0},
                "humidity": {"afternoon": 52.0},
                "precipitation": {"total": 0.0},
                "temperature": {
                    "min": 293.37,
                    "max": 304.57,
                    "afternoon": 301.28,
                    "night": 295.94,
                    "evening": 303.74,
                    "morning": 293.55,
                },
                "pressure": {"afternoon": 1013.0},
                "wind": {"max": {"speed": 7.72, "direction": 180.0}},
            }
        ),
    ]

    assert api_results == expected_results


@pytest.mark.asyncio()
async def test_weather_data_fetcher_incorrect_params():
    fetcher = WeatherDataFetcher()

    api_results, api_errors = await fetcher.fetch_weather_data(
        latitude="1234",
        longitude="1234",
        dates=[
            datetime.date(2024, 9, 27),
        ],
    )

    assert not api_results
    assert api_errors == [
        {
            "date": datetime.date(2024, 9, 27),
            "message": {
                "code": "400",
                "message": "The valid range of latitude in degrees is -90 and +90 for the southern and northern hemisphere, respectively",
                "parameters": ["lat"],
            },
        }
    ]


@pytest.mark.asyncio()
async def test_fetch_coordinates():
    fetcher = WeatherDataFetcher()
    results = await fetcher.fetch_coordinates("Santa Pola")

    assert len(results) > 0
    assert all(isinstance(result, GeocodingResult) for result in results)


@pytest.mark.asyncio()
async def test_fetch_coordinates_nonexisent():
    fetcher = WeatherDataFetcher()
    results = await fetcher.fetch_coordinates("Benipavel")

    assert len(results) == 0
