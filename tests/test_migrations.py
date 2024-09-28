import pytest
from sqlalchemy import text

from app.core.database import sessionmanager


@pytest.mark.asyncio
async def test_run_migrations(run_migrations_fixture):
    # This test will run migrations and check if tables are created
    async with sessionmanager.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in result]

        # Add assertions to check if expected tables are present
        assert "weather_daily_summaries" in tables
        # Add more assertions for other expected tables
