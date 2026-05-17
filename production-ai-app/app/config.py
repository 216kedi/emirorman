"""Centralised settings loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "production-ai-app"
    version: str = "0.1.0"
    environment: str = "development"

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    vector_db_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
