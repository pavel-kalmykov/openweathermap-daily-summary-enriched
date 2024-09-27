from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import run_migrations, sessionmanager
from app.core.logging import logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting up...")

    logger.info("Run alembic upgrade head...")
    await run_migrations()
    logger.info("Migrations successfully run")

    yield

    await sessionmanager.close()

    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan, port=settings.app_port)
