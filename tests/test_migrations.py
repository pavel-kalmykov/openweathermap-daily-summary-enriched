import pytest
from app.core.database import sessionmanager
from sqlalchemy import text


@pytest.mark.asyncio()
@pytest.mark.usefixtures("_run_migrations_fixture")
async def test_run_migrations():
    # This test will run migrations (by fixture) and check if tables are created
    async with sessionmanager.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in result]

        assert "weather_daily_summaries" in tables
