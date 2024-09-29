from datetime import date
from typing import Callable

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import settings


@pytest.mark.asyncio
async def test_get_weather_by_coordinates(
    test_client: TestClient,
    mock_weather_api_response: Callable,
    respx_mock: respx.Router,
):
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_response(date(2024, 9, 27))
    )

    response = test_client.get(
        "/weather/enriched-day-summary",
        params={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_date": "2024-09-27",
            "end_date": "2024-09-27",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["weather_data"]) == 1
    assert data["weather_data"][0]["latitude"] == 40.7128
    assert data["weather_data"][0]["longitude"] == -74.0060
    assert data["weather_data"][0]["date"] == "2024-09-27"
    assert "temp_min" in data["weather_data"][0]
    assert "temp_max" in data["weather_data"][0]
    assert "precipitation_total" in data["weather_data"][0]


@pytest.mark.asyncio
async def test_get_weather_by_location(
    test_client: TestClient,
    mock_weather_api_response: Callable,
    respx_mock: respx.Router,
):
    respx_mock.get(settings.geocoding_api_url).mock(
        return_value=Response(
            200,
            json=[
                {
                    "name": "New York",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "country": "US",
                    "state": "New York",
                }
            ],
        )
    )
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=mock_weather_api_response(date(2024, 9, 27))
    )

    response = test_client.get(
        "/weather/enriched-day-summary",
        params={
            "location": "New York",
            "start_date": "2024-09-27",
            "end_date": "2024-09-27",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["weather_data"]) == 1
    assert data["weather_data"][0]["latitude"] == 40.7128
    assert data["weather_data"][0]["longitude"] == -74.0060
    assert data["weather_data"][0]["date"] == "2024-09-27"


@pytest.mark.asyncio
async def test_get_weather_invalid_params(test_client: TestClient):
    response = test_client.get(
        "/weather/enriched-day-summary",
        params={"start_date": "2024-09-27", "end_date": "2024-09-27"},
    )

    assert response.status_code == 400
    data = response.json()
    assert (
        "Provide either latitude and longitude OR location"
        in data["errors"][0]["message"]
    )


@pytest.mark.asyncio
async def test_get_weather_all_params(test_client: TestClient):
    response = test_client.get(
        "/weather/enriched-day-summary",
        params={
            "start_date": "2024-09-27",
            "end_date": "2024-09-27",
            "location": "New York",
            "latitude": 37.8267,
            "longitude": -122.4233,
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert (
        "Provide either latitude and longitude OR location, not both"
        in data["errors"][0]["message"]
    )


@pytest.mark.asyncio
async def test_get_weather_date_range_too_large(test_client: TestClient):
    response = test_client.get(
        "/weather/enriched-day-summary",
        params={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_date": "2024-09-01",
            "end_date": "2024-10-15",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert len(data["errors"]) > 0
    assert "Date range exceeds maximum allowed" in data["errors"][0]["message"]


@pytest.mark.asyncio
async def test_get_weather_api_error(test_client: TestClient, respx_mock: respx.Router):
    respx_mock.get(settings.openweathermap_day_summary_url).mock(
        return_value=Response(401, json={"cod": "401", "message": "Invalid API key"})
    )

    response = test_client.get(
        "/weather/enriched-day-summary",
        params={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_date": "2024-09-27",
            "end_date": "2024-09-27",
        },
    )

    assert response.status_code == 206
    data = response.json()
    assert len(data["weather_data"]) == 0
    assert len(data["errors"]) > 0
    assert any(
        "Error fetching weather daily summary from API" in str(error)
        for error in data["errors"]
    )
