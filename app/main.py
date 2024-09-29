from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import run_migrations, sessionmanager
from app.core.exceptions import WeatherServiceInputError
from app.core.logging import logger
from app.routes import weather


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting up...")

    logger.info("Run alembic upgrade head...")
    await run_migrations()
    logger.info("Migrations successfully run")

    yield

    await sessionmanager.close()

    logger.info("Shutting down...")


app = FastAPI(
    title="Enriched Weather API",
    description="""
This API provides enriched weather data for specific locations and date ranges.
It fetches data from OpenWeatherMap and enhances it with additional calculations and metrics.

## Features

- Retrieve weather data by coordinates or location name
- Get enriched daily summaries including derived weather indices
- Historical weather data retrieval

## Usage

To use this API, you need to provide a date range and either coordinates (latitude and longitude) or a location name.
The API will return detailed weather information for each day in the specified range.

For more detailed information on each endpoint, please refer to the specific endpoint documentation below.
    """,
    version="0.1.0",
    lifespan=lifespan,
    port=settings.app_port,
    openapi_tags=[
        {
            "name": "Weather",
            "description": "Operations related to weather data retrieval and processing",
        },
    ],
)


@app.exception_handler(WeatherServiceInputError)
def weather_service_error_handler(
    _req: Request, exc: WeatherServiceInputError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "errors": [{"message": str(exc)}],
        },
    )


app.include_router(weather.router)
