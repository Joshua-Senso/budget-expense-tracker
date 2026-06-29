from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn
    redis_url: RedisDsn
    auth_jwks_url: str
    auth_jwt_issuer: str
    auth_jwt_audience: str

    @computed_field
    @property
    def sqlalchemy_database_url(self) -> str:
        database_url = str(self.database_url)
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
