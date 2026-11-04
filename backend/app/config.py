"""
Central place for environment-driven configuration.

Nothing here is hardcoded on purpose: whoever hosts this app should be able
to change the database and allowed frontend origins purely via environment
variables / a .env file, with no code changes.
"""
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./zaradera.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def business_today():
    """Nigeria uses UTC+1 year-round, independent of the server timezone."""
    return datetime.now(timezone(timedelta(hours=1))).date()
