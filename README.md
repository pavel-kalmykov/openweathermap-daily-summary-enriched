# Enriched Weather API

An API that fetches daily weather summaries from the OpenWeatherMap API and enriches them with additional calculations.

## Features

- Retrieve weather data by coordinates or location name
- Get enriched daily summaries including derived weather indices
- Historical weather data retrieval (day range)

### Technical Stack

Overall, these are the technologies used to build this project:

- FastAPI for building the API endpoints
- PostgreSQL for database storage
- Polars for data manipulation (enrichment)
- HTTPX (async API) for HTTP requests
- SQLAlchemy (async API) for database access
- pytest for testing
- Docker/Docker Compose for containerization
- Poetry for dependency management and packaging
- Ruff for linting and formatting
- MkDocs for documentation

## Quick Start

To get started with the Enriched Weather API, follow these steps:

1. Clone the repository if not done already.
2. Set up your environment variables in a new `.env` file. Use the `.env.example` file as a template.
3. Launch the application with Docker Compose: `docker-compose up -d`
4. Access the application at whatever port you set in your `.env` file.

For more detailed instructions, please refer to the [Setup](docs/development/setup.md) guide.
