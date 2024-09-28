import pytest

from app.core.database import run_migrations


@pytest.fixture(scope="session")
async def run_migrations_fixture():
    # Override database URL for testing
    await run_migrations()
