## Project Setup

### Prerequisites

Before running the project, you need to have [Docker](https://www.docker.com/) and Docker Compose installed on your system.
In order to run any commands, you must have cloned the project repository to your local machine and be located in its root folder.

Additionally, you require an OpenWeatherMap API key for the weather service to work properly. The key's account must have access to the [One Call API 3.0](https://openweathermap.org/api/one-call-3) via subscription (it offers a free tier and limits to avoid any spending).

### Setup

1. Set up your environment variables in a new `.env` file. Use the `.env.example` file as a template.
2. Just build and start the containers:

```console
docker compose up --build [-d]
```

The API will be available at `http://localhost:APP_PORT`, `APP_PORT` being the port you specified in your `.env` file.
For the docs, you can access the MkDocs documentation at `http://localhost:MKDOCS_PORT`.
Lastly, you can access the PostgreSQL database at `localhost:DB_PORT` with the credentials specified in your `.env` file.

### Using the API

The easiest way to try the API operations is by navigating `http://localhost:APP_PORT/docs`.
Additionally, the API is also documented in the MkDocs server: [API Reference](../api/weather.md).

## Development

For local development without Docker:

1. Ensure you have [Python 3.12](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/) installed.
2. Configure your environment variables just like in the regular Docker setup.
3. Set up a local PostgreSQL instance (`docker compose up db`) or update the `DB_`-related variables in your environment to point to your instance.
4. Install the Poetry environment by running `poetry install` and start the development server with `fastapi run`.

### Running Tests

To run the tests, just execute `pytest` with any additional parameter you want.

Some tests require a valid OpenWeatherMap API key, so be sure you have one.
