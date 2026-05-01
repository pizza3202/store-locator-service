from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Store Locator Service"
    app_env: str = "development"
    secret_key: str = "change_me"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    database_url: str = "postgresql+psycopg2://yutingbu@localhost:5432/store_locator"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    geocoding_provider: str = "nominatim"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
