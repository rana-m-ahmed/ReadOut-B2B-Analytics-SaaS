"""Live Supabase round-trip coverage for dashboard widget routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

from app.db.models import DashboardCreate, WorkspaceCreate
from app.db.repositories import DashboardRepository, DatasetRepository, WorkspaceRepository
from app.nlq.schemas import analytics_intent_adapter

API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _has_live_credentials() -> bool:
    values = _load_env_file(API_ENV_FILE)
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET")
    return all(values.get(name, "").strip() for name in required)


def _build_auth_token(env: dict[str, str], user_id: UUID) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": False},
        },
        env["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )


def test_widget_pin_list_reorder_delete_live_round_trip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _has_live_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    env = _load_env_file(API_ENV_FILE)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    from app.core.config import get_settings
    from app.db.supabase_client import reset_supabase_client
    from app.main import create_app

    get_settings.cache_clear()
    reset_supabase_client()

    workspace_repository = WorkspaceRepository()
    dashboard_repository = DashboardRepository()
    dataset_repository = DatasetRepository()
    supabase = workspace_repository._client
    demo_dataset = dataset_repository.get_demo_dataset()
    if demo_dataset is None:
        pytest.skip("requires the seeded public demo dataset")

    client = TestClient(create_app())
    user_id: UUID | None = None
    workspace_id: UUID | None = None
    try:
        try:
            user_response = supabase.auth.admin.create_user(
                {
                    "email": f"routes-widgets-{uuid4().hex}@example.com",
                    "password": f"T3st!{uuid4().hex}",
                    "email_confirm": True,
                }
            )
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable: {exc}")

        user_id = UUID(user_response.user.id)
        workspace = workspace_repository.create(
            user_id,
            WorkspaceCreate(name="Routes Widgets Workspace", slug=f"routes-widgets-{uuid4().hex[:8]}"),
        )
        workspace_id = workspace.id
        dashboard = dashboard_repository.create(
            workspace.id,
            DashboardCreate(created_by=user_id, name="Pinned Analytics"),
        )
        headers = {"Authorization": f"Bearer {_build_auth_token(env, user_id)}"}

        intent = analytics_intent_adapter.validate_python(
            {
                "intent": "single_metric",
                "metric": "revenue",
                "aggregation": "sum",
                "group_by": [],
                "date_range": None,
                "filters": [],
                "sort": None,
                "limit": 1,
                "chart_hint": "metric",
            }
        )
        with (
            patch("app.api.routes_ask.get_intent", new=AsyncMock(return_value=intent)),
            patch("app.api.routes_ask.generate_summary", new=AsyncMock(return_value="Total revenue result.")),
        ):
            first_ask = client.post(
                "/ask",
                json={"dataset_id": str(demo_dataset.id), "question": "What is total revenue?"},
                headers=headers,
            )
            second_ask = client.post(
                "/ask",
                json={"dataset_id": str(demo_dataset.id), "question": "Show total revenue again."},
                headers=headers,
            )

        assert first_ask.status_code == 200, first_ask.text
        assert second_ask.status_code == 200, second_ask.text
        first_ask_payload = first_ask.json()
        second_ask_payload = second_ask.json()
        assert first_ask_payload["chart"] is not None
        assert first_ask_payload["query_plan"] is not None

        first_pin = client.post(
            "/widgets",
            json={
                "dashboard_id": str(dashboard.id),
                "source_type": "ask_message",
                "source_id": first_ask_payload["answer_id"],
                "title": "Revenue One",
            },
            headers=headers,
        )
        second_pin = client.post(
            "/widgets",
            json={
                "dashboard_id": str(dashboard.id),
                "source_type": "ask_message",
                "source_id": second_ask_payload["answer_id"],
                "title": "Revenue Two",
            },
            headers=headers,
        )
        assert first_pin.status_code == 201, first_pin.text
        assert second_pin.status_code == 201, second_pin.text

        first_widget = first_pin.json()
        second_widget = second_pin.json()
        assert first_widget["config"]["chart_payload"] == first_ask_payload["chart"]
        assert first_widget["config"]["query_plan"] == first_ask_payload["query_plan"]

        listed = client.get(f"/dashboards/{dashboard.id}/widgets", headers=headers)
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [
            first_widget["id"],
            second_widget["id"],
        ]

        reordered = client.patch(
            f"/dashboards/{dashboard.id}/layout",
            json={
                "widgets": [
                    {"widget_id": second_widget["id"], "position": 0},
                    {"widget_id": first_widget["id"], "position": 1},
                ]
            },
            headers=headers,
        )
        assert reordered.status_code == 200, reordered.text
        assert reordered.json()["layout"] == [
            {"widget_id": second_widget["id"], "position": 0},
            {"widget_id": first_widget["id"], "position": 1},
        ]

        listed_after_reorder = client.get(f"/dashboards/{dashboard.id}/widgets", headers=headers)
        assert listed_after_reorder.status_code == 200
        assert [
            (item["id"], item["position"])
            for item in listed_after_reorder.json()
        ] == [
            (second_widget["id"], 0),
            (first_widget["id"], 1),
        ]
        persisted_dashboard = dashboard_repository.get_by_id(workspace.id, dashboard.id)
        assert persisted_dashboard is not None
        assert persisted_dashboard.layout == reordered.json()["layout"]

        deleted = client.delete(f"/widgets/{first_widget['id']}", headers=headers)
        assert deleted.status_code == 204
        final_list = client.get(f"/dashboards/{dashboard.id}/widgets", headers=headers)
        assert final_list.status_code == 200
        assert [item["id"] for item in final_list.json()] == [second_widget["id"]]
        dashboard_after_delete = dashboard_repository.get_by_id(workspace.id, dashboard.id)
        assert dashboard_after_delete is not None
        assert dashboard_after_delete.layout == [
            {"widget_id": second_widget["id"], "position": 0}
        ]
    finally:
        if user_id is not None and workspace_id is not None:
            workspace_repository.delete(user_id, workspace_id)
        if user_id is not None:
            supabase.auth.admin.delete_user(str(user_id))
