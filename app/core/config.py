from typing import Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    app_port: int
    db_url: str | None = None
    log_level: str = "INFO"
    openweathermap_day_summary_url: str = (
        "https://api.openweathermap.org/data/3.0/onecall/day_summary"
    )
    geocoding_api_url: str = "http://api.openweathermap.org/geo/1.0/direct"
    geocoding_results_limit: int = 5
    openweathermap_max_calls_per_minute: int = 60
    weather_service_max_date_range: int = 31

    @property
    def database_url(self: Self) -> str:
        return (
            self.db_url
            or f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
