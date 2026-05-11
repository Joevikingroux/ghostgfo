"""Application settings loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "GhostCFO"
    app_env: Literal["development", "staging", "production"] = "development"
    secret_key: str = "change-me"
    base_url: str = "https://ghostcfo.numbers10.co.za"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+psycopg://ghostcfo:ghostcfo@db:5432/ghostcfo"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # OpenRouter (LLM)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_temperature: float = 0.4
    llm_max_tokens: int = 1200
    llm_timeout_seconds: int = 60


    # Email (Resend — resend.com)
    resend_api_key: str = ""
    from_email: str = "reports@ghostcfo.numbers10.co.za"
    from_name: str = "Ghost CFO"

    # Storage
    upload_dir: Path = Path("/app/uploads")
    reports_dir: Path = Path("/app/reports")

    # Agent
    agent_encryption_key: str = "change-me-32-bytes"

    # PayFast
    payfast_merchant_id: str = ""
    payfast_merchant_key: str = ""
    payfast_passphrase: str = ""
    payfast_sandbox: bool = True   # Set False in production after testing

    # Payroll
    payroll_db_enabled: bool = False
    payroll_journal_gl_account: str = "7100"

    # Branding
    brand_primary: str = "#2DD4BF"
    brand_secondary: str = "#06B6D4"
    brand_footer: str = (
        "Powered by Numbers10 Technology Solutions | numbers10.co.za"
    )

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 60 * 24
    jwt_refresh_days: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
