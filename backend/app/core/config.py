from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Wireless Communication Intelligence Platform"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    database_url: str = "postgresql+psycopg://wireless:wireless@postgres:5432/wireless"
    redis_url: str = "redis://redis:6379/0"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    jwt_secret: str = "change-me-in-production"  # nosec B105 - local default, override in deployed env
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "admin"  # nosec B105 - local default, override in deployed env

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    local_llama_base_url: AnyHttpUrl | None = None
    default_llm_provider: str = "openai"

    tavily_api_key: str | None = None
    google_search_api_key: str | None = None
    google_search_cx: str | None = None

    rate_limit: str = "60/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
