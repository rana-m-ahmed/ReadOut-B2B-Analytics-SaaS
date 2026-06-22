"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Single source of truth for backend configuration."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore",
    )

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_ANON_KEY: str
    GROQ_API_KEY: str
    GROQ_PRIMARY_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)
    ENVIRONMENT: str = "development"
    MAX_UPLOAD_MB: int = 25
    QUERY_TIMEOUT_SECONDS: int = 10
    MAX_RESULT_ROWS: int = 500
    MAX_CHART_PAYLOAD_KB: int = 50
    ANON_SESSION_TTL_HOURS: int = 72
    ASK_CONTEXT_TURN_LIMIT: int = 4
    ASK_RATE_LIMIT_REQUESTS: int = Field(default=20, ge=1)
    ASK_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)
    UPLOAD_URL_RATE_LIMIT_REQUESTS: int = Field(default=10, ge=1)
    UPLOAD_URL_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)

    # Groq rate limits are intentionally not configuration values here.
    # Free-tier RPM/RPD/TPM limits change without notice; Phase 4's groq_client
    # must react to live 429 and rate-limit headers instead of stale constants.

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> list[str]:
        """Normalize ALLOWED_ORIGINS from env input into a clean string list."""
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("ALLOWED_ORIGINS must be a comma-separated string or list of strings")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
