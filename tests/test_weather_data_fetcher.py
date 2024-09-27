import datetime

import pytest

from app.usecases.weather_data_fetcher import WeatherDataFetcher


@pytest.mark.asyncio
async def test_weather_data_processor():
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
    assert api_results == [
        {
            "lat": 38.2653307,
            "lon": -0.6988391,
            "tz": "+02:00",
            "date": "2024-09-27",
            "units": "standard",
            "cloud_cover": {"afternoon": 13.32},
            "humidity": {"afternoon": 42.45},
            "precipitation": {"total": 0.07},
            "temperature": {
                "min": 295.79,
                "max": 302.02,
                "afternoon": 300.78,
                "night": 299.43,
                "evening": 301.13,
                "morning": 296.86,
            },
            "pressure": {"afternoon": 1014.06},
            "wind": {"max": {"speed": 7.81, "direction": 310.84}},
        },
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
        },
    ]


@pytest.mark.asyncio
async def test_weather_data_processor_incorrect_params():
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
            "error": {
                "code": "400",
                "message": "The valid range of latitude in degrees is -90 and +90 for the southern and northern hemisphere, respectively",
                "parameters": ["lat"],
            },
        }
    ]
