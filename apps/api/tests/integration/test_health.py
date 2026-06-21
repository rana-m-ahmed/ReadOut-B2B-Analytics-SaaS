from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.core.config import Settings

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "jwt-secret")
os.environ.setdefault("SUPABASE_ANON_KEY", "anon-key")
os.environ.setdefault("GROQ_API_KEY", "groq-key")

from app.main import create_app


def test_health_returns_ok_with_environment() -> None:
    settings = Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        ENVIRONMENT="test",
    )
    client = TestClient(create_app(settings=settings))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "test"}
