from pydantic import PostgresDsn
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
    env: str
    log_level: str = "INFO"
    openweathermap_day_summary_url: str = (
        "https://api.openweathermap.org/data/3.0/onecall/day_summary"
    )
    openweathermap_max_calls_per_minute: int = 60

    @property
    def database_url(self) -> PostgresDsn:
        return PostgresDsn(
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
