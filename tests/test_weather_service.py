from contextlib import suppress
from datetime import date, timedelta
from typing import AsyncGenerator, Callable

import pytest
import pytest_mock
import respx
from httpx import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import sessionmanager
from app.models import WeatherDailySummary
from app.repositories import WeatherRepository
from app.schemas import (
    GeocodingResult,
    WeatherServiceResponse,
)
from app.schemas.weather import WeatherSummaryResponse
from app.usecases import WeatherDataFetcher, WeatherDataProcessor, WeatherService


@pytest.fixture(scope="function")
async def db_session(run_migrations_fixture) -> AsyncGenerator[AsyncSession, None]:
    with suppress(SQLAlchemyError):
        async with sessionmanager.session() as session:
            yield session
            raise SQLAlchemyError("We must not commit, but rollback in every test case")


@pytest.fixture
def weather_data_fetcher() -> WeatherDataFetcher:
    return WeatherDataFetcher()


@pytest.fixture
def weather_data_processor() -> WeatherDataProcessor:
    return WeatherDataProcessor()


@pytest.fixture
def weather_repository(db_session) -> WeatherRepository:
    return WeatherRepository(db_session)


@pytest.fixture
def weather_service(
    weather_repository: WeatherRepository,
    weather_data_fetcher: WeatherDataFetcher,
    weather_data_processor: WeatherDataProcessor,
) -> WeatherService:
    return WeatherService(
        weather_repository, weather_data_fetcher, weather_data_processor
    )


@pytest.fixture
def mock_weather_api_response():
    def _mock_response(
        test_date: date, latitude: float = 40.7128, longitude: float = -74.0060
    ):
        return Response(
            200,
            json={
                "lat": latitude,
                "lon": longitude,
                "tz": "+00:00",
                "date": test_date.isoformat(),
                "units": "standard",
                "cloud_cover": {"afternoon": 50},
                "humidity": {"afternoon": 60},
                "precipitation": {"total": 5},
                "temperature": {
                    "min": 288.15,
                    "max": 298.15,
                    "afternoon": 295.15,
                    "night": 290.15,
                    "evening": 293.15,
                    "morning": 289.15,
                },
                "pressure": {"afternoon": 1013},
                "wind": {"max": {"speed": 5, "direction": 180}},
            },
        )

    return _mock_response


@pytest.fixture
def mock_weather_api_error_response():
    def _mock_error_response(error_message: str):
        return Response(400, json={"cod": "400", "message": error_message})

    return _mock_error_response


@pytest.mark.asyncio
async def test_get_weather_data_new_data(
    weather_service: WeatherService, mock_weather_api_response, respx_mock
):
    test_date = date(2024, 9, 1)
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_response(test_date)
    )

    response = await weather_service.get_weather_data(
        40.7128, -74.0060, test_date, test_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert len(response.weather_data) == 1
    assert not response.errors
    weather_summary = response.weather_data[0]
    assert isinstance(weather_summary, WeatherSummaryResponse)
    assert weather_summary.latitude == 40.7128
    assert weather_summary.longitude == -74.0060
    assert weather_summary.date == test_date
    assert weather_summary.temp_min == pytest.approx(288.15)
    assert weather_summary.temp_max == pytest.approx(298.15)
    assert weather_summary.temp_afternoon == pytest.approx(295.15)
    assert weather_summary.humidity_afternoon == 60
    assert weather_summary.precipitation_total == 5
    assert weather_summary.pressure_afternoon == 1013
    assert weather_summary.wind_speed_max == 5
    assert weather_summary.wind_direction_max == 180


@pytest.mark.asyncio
async def test_get_weather_data_partial_existing(
    weather_service: WeatherService,
    db_session: AsyncGenerator[AsyncSession, None],
    mock_weather_api_response: Callable,
    respx_mock: respx.Router,
):
    existing_date = date(2024, 9, 1)
    existing_summary = WeatherDailySummary(
        date=existing_date,
        latitude=40.7128,
        longitude=-74.0060,
        timezone="+00:00",
        temp_min=288.15,
        temp_max=298.15,
        temp_afternoon=295.15,
        temp_night=290.15,
        temp_evening=293.15,
        temp_morning=289.15,
        temp_range=10.0,
        cloud_cover_afternoon=50,
        humidity_afternoon=60,
        precipitation_total=5.0,
        pressure_afternoon=1013,
        wind_speed_max=5.0,
        wind_direction_max=180,
        temp_variability_index=0.033,
        season="Summer",
        extreme_temperature=False,
        extreme_precipitation=False,
        extreme_wind=False,
        humidex=300.15,
        precipitation_intensity="Light",
    )
    db_session.add(existing_summary)
    await db_session.commit()

    missing_date = existing_date + timedelta(days=1)
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_response(missing_date)
    )

    response = await weather_service.get_weather_data(
        40.7128, -74.0060, existing_date, missing_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert len(response.weather_data) == 2
    assert not response.errors
    weather_summary1, weather_summary2 = response.weather_data
    assert weather_summary1.date == existing_date
    assert weather_summary1.temp_min == pytest.approx(288.15)
    assert weather_summary2.date == missing_date
    assert weather_summary2.temp_min == pytest.approx(288.15)
    assert weather_summary1.date < weather_summary2.date
    assert len(set(summary.date for summary in response.weather_data)) == 2


@pytest.mark.asyncio
async def test_get_weather_data_invalid_coordinates(
    weather_service: WeatherService,
    mock_weather_api_error_response: Callable,
    respx_mock: respx.Router,
):
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_error_response("wrong latitude")
    )

    start_date = date(2024, 9, 1)
    response = await weather_service.get_weather_data(
        91.0, -74.0060, start_date, start_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert not response.weather_data
    assert len(response.errors) == 1
    assert "wrong latitude" in response.errors[0]["error"]["message"]


@pytest.mark.asyncio
async def test_get_weather_data_database_error(
    weather_service: WeatherService, mocker: pytest_mock.MockerFixture
):
    start_date = date(2024, 9, 1)
    mocker.patch.object(
        weather_service.weather_repository,
        "get_daily_summaries",
        side_effect=SQLAlchemyError("Database connection error"),
    )

    with pytest.raises(SQLAlchemyError):
        await weather_service.get_weather_data(
            40.7128, -74.0060, start_date, start_date
        )


@pytest.mark.asyncio
async def test_get_weather_data_large_date_range(
    weather_service: WeatherService,
):
    start_date = date(2024, 8, 29)
    end_date = date(2024, 9, 30)

    response = await weather_service.get_weather_data(
        40.7128, -74.0060, start_date, end_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert not response.weather_data
    assert len(response.errors) == 1
    assert "Date range exceeds maximum allowed" in response.errors[0]


@pytest.mark.asyncio
async def test_get_weather_data_by_name(
    weather_service: WeatherService,
    mock_weather_api_response: Callable,
    respx_mock: respx.Router,
):
    location_name = "New York"
    test_date = date(2024, 9, 1)

    # Mock the geocoding API call
    respx_mock.get(settings.geocoding_api_url).mock(
        return_value=Response(
            200,
            json=[
                {
                    "name": "New York",
                    "local_names": {"en": "New York"},
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "country": "US",
                    "state": "New York",
                }
            ],
        )
    )

    # Mock the weather data API call
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_response(test_date, 40.7128, -74.0060)
    )

    response = await weather_service.get_weather_data_by_name(
        location_name, test_date, test_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert len(response.weather_data) == 1
    assert not response.errors
    assert len(response.geocoding_results) == 1
    assert isinstance(response.weather_data[0], WeatherSummaryResponse)
    assert isinstance(response.geocoding_results[0], GeocodingResult)
    assert response.weather_data[0].latitude == 40.7128
    assert response.weather_data[0].longitude == -74.0060
    assert response.weather_data[0].date == test_date


@pytest.mark.asyncio
async def test_get_weather_data_by_name_multiple_locations(
    weather_service: WeatherService, respx_mock: respx.Router
):
    location_name = "Springfield"
    test_date = date(2024, 9, 1)

    # Mock the geocoding API call to return multiple results
    respx_mock.get(settings.geocoding_api_url).mock(
        return_value=Response(
            200,
            json=[
                {
                    "name": "Springfield",
                    "local_names": {"en": "Springfield"},
                    "lat": 39.7817,
                    "lon": -89.6501,
                    "country": "US",
                    "state": "Illinois",
                },
                {
                    "name": "Springfield",
                    "local_names": {"en": "Springfield"},
                    "lat": 37.2090,
                    "lon": -93.2923,
                    "country": "US",
                    "state": "Missouri",
                },
            ],
        )
    )

    response = await weather_service.get_weather_data_by_name(
        location_name, test_date, test_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert not response.weather_data
    assert len(response.errors) == 1
    assert "Multiple locations found" in response.errors[0]
    assert len(response.geocoding_results) == 2
    assert all(
        isinstance(result, GeocodingResult) for result in response.geocoding_results
    )


@pytest.mark.asyncio
async def test_get_weather_data_by_name_large_date_range(
    weather_service: WeatherService,
):
    location_name = "New York"
    start_date = date(2024, 8, 28)
    end_date = date(2024, 9, 30)

    response = await weather_service.get_weather_data_by_name(
        location_name, start_date, end_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert not response.weather_data
    assert len(response.errors) == 1
    assert "Date range exceeds maximum allowed" in response.errors[0]


@pytest.mark.asyncio
async def test_get_weather_data_by_name_no_geocoding_results(
    weather_service: WeatherService, respx_mock
):
    location_name = "Benipavel"
    test_date = date(2023, 9, 1)

    # Mock the geocoding API call to return an empty list
    respx_mock.get(settings.geocoding_api_url).mock(return_value=Response(200, json=[]))

    response = await weather_service.get_weather_data_by_name(
        location_name, test_date, test_date
    )

    assert isinstance(response, WeatherServiceResponse)
    assert not response.weather_data
    assert len(response.errors) == 1
    assert "Could not find coordinates for location" in response.errors[0]
    assert not response.geocoding_results
