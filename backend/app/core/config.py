"""Application configuration loaded from environment (.env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    frontend_port: int = 5245
    backend_port: int = 8072
    postgres_port: int = 5504
    pgadmin_port: int = 5122

    postgres_user: str = "twin"
    postgres_password: str = "twin_secret"
    postgres_db: str = "financial_twin"
    database_url: str = "postgresql+asyncpg://twin:twin_secret@db:5432/financial_twin"

    assumption_set: str = "ID-2026-09"
    engine_version: str = "2.0.0"

    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    llm_timeout_seconds: int = 8

    cors_origins: str = "http://localhost:5245"
    public_api_url: str = "http://localhost:8072"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
