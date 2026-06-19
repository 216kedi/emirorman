from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "production-ai-app"
    version: str = "0.2.0"
    environment: Literal["development", "staging", "production"] = "development"

    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm_provider: Literal["anthropic", "openai"] = "anthropic"
    default_llm_model: str = "claude-opus-4-7"
    default_embedding_model: str = "text-embedding-3-large"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "prod_ai_app"

    redis_url: str = "redis://localhost:6379/0"
    semantic_cache_threshold: float = Field(default=0.93, ge=0.0, le=1.0)

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    otel_exporter_otlp_endpoint: str = ""

    enable_input_guard: bool = True
    enable_output_guard: bool = True

    api_key: str = ""
    rate_limit_per_minute: int = 60

    # WhatsApp / Meta Cloud API (Elis Evleri sensor alarm notifications)
    building_name: str = "Elis Evleri"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v21.0"
    whatsapp_template_name: str = "elis_alarm"
    whatsapp_template_lang: str = "tr"
    whatsapp_recipients: str = ""  # comma-separated E.164 numbers, e.g. +905551112233,+905554445566
    alert_cooldown_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
