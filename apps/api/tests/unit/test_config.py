from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


REQUIRED_SECRET_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_ANON_KEY",
    "GROQ_API_KEY",
)


def clear_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in REQUIRED_SECRET_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key in (
        "GROQ_PRIMARY_MODEL",
        "GROQ_FALLBACK_MODEL",
        "ALLOWED_ORIGINS",
        "ENVIRONMENT",
        "MAX_UPLOAD_MB",
        "QUERY_TIMEOUT_SECONDS",
        "MAX_RESULT_ROWS",
        "MAX_CHART_PAYLOAD_KB",
        "ANON_SESSION_TTL_HOURS",
        "ASK_CONTEXT_TURN_LIMIT",
    ):
        monkeypatch.delenv(key, raising=False)


def set_required_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "jwt-secret")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")


def test_missing_required_secret_env_vars_raise_clear_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_settings_env(monkeypatch)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_text = str(exc_info.value)
    for field_name in REQUIRED_SECRET_KEYS:
        assert field_name in error_text


def test_optional_defaults_apply_when_env_vars_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_env(monkeypatch)
    set_required_settings_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.GROQ_PRIMARY_MODEL == "llama-3.3-70b-versatile"
    assert settings.GROQ_FALLBACK_MODEL == "llama-3.1-8b-instant"
    assert settings.ALLOWED_ORIGINS == []
    assert settings.ENVIRONMENT == "development"
    assert settings.MAX_UPLOAD_MB == 25
    assert settings.QUERY_TIMEOUT_SECONDS == 10
    assert settings.MAX_RESULT_ROWS == 500
    assert settings.MAX_CHART_PAYLOAD_KB == 50
    assert settings.ANON_SESSION_TTL_HOURS == 72
    assert settings.ASK_CONTEXT_TURN_LIMIT == 4


def test_allowed_origins_parses_comma_separated_env_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_settings_env(monkeypatch)
    set_required_settings_env(monkeypatch)
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000, https://app.readout.ai ,https://admin.readout.ai",
    )

    settings = Settings(_env_file=None)

    assert settings.ALLOWED_ORIGINS == [
        "http://localhost:3000",
        "https://app.readout.ai",
        "https://admin.readout.ai",
    ]
