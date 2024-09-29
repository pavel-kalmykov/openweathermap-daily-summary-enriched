import contextlib
from typing import Any, AsyncIterator, Self

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()
DB_NOT_INIT_ERR_MSG = "DatabaseSessionManager is not initialized"
# Heavily inspired by https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308


class DatabaseSessionManager:
    def __init__(self: Self, host: str, **engine_kwargs: dict[str, Any]):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self: Self):
        if self._engine is None:
            raise Exception(DB_NOT_INIT_ERR_MSG)
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self: Self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception(DB_NOT_INIT_ERR_MSG)

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self: Self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception(DB_NOT_INIT_ERR_MSG)

        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.database_url)


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


async def run_migrations():
    def run_upgrade(connection: AsyncConnection, cfg: Config):
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    async with sessionmanager.connect() as connection:
        await connection.run_sync(run_upgrade, Config("alembic.ini"))
