from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.routes_ask import router as ask_router
from app.api.routes_datasets import router as datasets_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.rate_limit import (
    InMemorySlidingWindowRateLimitStore,
    build_user_rate_limit_dependency,
    enforce_ask_rate_limit,
    enforce_rate_limit_for_user,
    enforce_upload_url_rate_limit,
    get_rate_limit_store,
)
from app.core.errors import RateLimitedError
from app.security.auth_guard import CurrentUser, get_current_user


def _test_settings(**overrides: int) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        **overrides,
    )


def _find_api_route(router: APIRouter, path: str, method: str) -> APIRoute:
    for route in router.routes:
        if isinstance(route, APIRoute) and route.path == path and method.upper() in route.methods:
            return route
    raise AssertionError(f"Route {method} {path} not found")


def _build_limited_app(settings: Settings, store: InMemorySlidingWindowRateLimitStore) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    test_user = CurrentUser(user_id=uuid4(), is_anonymous=False)
    limiter = build_user_rate_limit_dependency(
        scope="test_scope",
        limit_setting="ASK_RATE_LIMIT_REQUESTS",
        window_setting="ASK_RATE_LIMIT_WINDOW_SECONDS",
    )

    @app.get("/limited", dependencies=[Depends(limiter)])
    async def limited_endpoint() -> dict[str, bool]:
        return {"ok": True}

    async def current_user_dependency() -> CurrentUser:
        return test_user

    app.dependency_overrides[get_current_user] = current_user_dependency
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_rate_limit_store] = lambda: store
    return TestClient(app)


def test_requests_under_limit_pass() -> None:
    user_id = uuid4()
    store = InMemorySlidingWindowRateLimitStore()

    enforce_rate_limit_for_user(
        user_id,
        scope="ask",
        limit=2,
        window_seconds=60,
        store=store,
        now=0.0,
    )
    enforce_rate_limit_for_user(
        user_id,
        scope="ask",
        limit=2,
        window_seconds=60,
        store=store,
        now=10.0,
    )


def test_requests_over_limit_return_typed_429() -> None:
    settings = _test_settings(ASK_RATE_LIMIT_REQUESTS=2, ASK_RATE_LIMIT_WINDOW_SECONDS=60)
    store = InMemorySlidingWindowRateLimitStore()
    client = _build_limited_app(settings, store)

    first = client.get("/limited")
    second = client.get("/limited")
    third = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "rate_limited"
    assert "Too many requests for test_scope" in third.json()["error"]["message"]


def test_limit_resets_after_window_elapses() -> None:
    user_id = uuid4()
    store = InMemorySlidingWindowRateLimitStore()

    enforce_rate_limit_for_user(
        user_id,
        scope="upload",
        limit=1,
        window_seconds=30,
        store=store,
        now=0.0,
    )

    with pytest.raises(RateLimitedError):
        enforce_rate_limit_for_user(
            user_id,
            scope="upload",
            limit=1,
            window_seconds=30,
            store=store,
            now=10.0,
        )

    enforce_rate_limit_for_user(
        user_id,
        scope="upload",
        limit=1,
        window_seconds=30,
        store=store,
        now=31.0,
    )


def test_ask_and_upload_url_routes_use_rate_limit_dependencies() -> None:
    ask_route = _find_api_route(ask_router, "/ask", "POST")
    upload_url_route = _find_api_route(datasets_router, "/datasets/upload-url", "POST")

    ask_dependencies = {dependency.call for dependency in ask_route.dependant.dependencies}
    upload_url_dependencies = {dependency.call for dependency in upload_url_route.dependant.dependencies}

    assert enforce_ask_rate_limit in ask_dependencies
    assert enforce_upload_url_rate_limit in upload_url_dependencies
