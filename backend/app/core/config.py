from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://petcare:petcare_local@localhost:5432/petcare"
    db_connect_timeout: int = Field(default=3, ge=1, le=30)

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if make_url(value).drivername != "postgresql+psycopg2":
            raise ValueError("DATABASE_URL must use postgresql+psycopg2")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
