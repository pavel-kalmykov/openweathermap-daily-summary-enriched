from contextlib import suppress
from datetime import date
from typing import AsyncGenerator, Callable

import pytest
from app.core.database import get_db_session, run_migrations, sessionmanager
from app.main import app
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="session")
async def _run_migrations_fixture():
    await run_migrations()


@pytest.fixture
async def test_client(
    _run_migrations_fixture: None,  # noqa: PT019
) -> AsyncGenerator[TestClient, None]:
    app.dependency_overrides[get_db_session] = get_test_db_session
    return TestClient(app)


@pytest.fixture
async def db_session(
    _run_migrations_fixture: None,
) -> AsyncGenerator[AsyncSession, None]:
    with suppress(SQLAlchemyError):
        async with sessionmanager.session() as session:
            yield session
            msg = "We must not commit, but rollback in every test case"
            raise SQLAlchemyError(msg)


async def get_test_db_session():
    with suppress(SQLAlchemyError):
        async with sessionmanager.session() as session:
            yield session
            msg = "We must not commit, but rollback in every test case"
            raise SQLAlchemyError(msg)


@pytest.fixture
def mock_weather_api_response() -> Callable[[date, float, float], Response]:
    def _mock_response(
        test_date: date, latitude: float = 40.7128, longitude: float = -74.0060
    ) -> Response:
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
