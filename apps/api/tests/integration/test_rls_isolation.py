from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError

from app.db.models import (
    AnomalyCreate,
    AskMessageCreate,
    AskSessionCreate,
    DashboardCreate,
    DatasetCreate,
    InsightCreate,
    WidgetCreate,
    WorkspaceCreate,
)
from app.db.repositories import (
    AnomalyRepository,
    AskMessageRepository,
    AskSessionRepository,
    DashboardRepository,
    DatasetRepository,
    InsightRepository,
    WidgetRepository,
    WorkspaceRepository,
)


API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


@dataclass
class _SessionContext:
    user_id: UUID
    access_token: str
    refresh_token: str | None
    is_anonymous: bool
    issued_via_fallback_jwt: bool = False


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _has_live_supabase_credentials() -> bool:
    if not API_ENV_FILE.exists():
        return False
    values = _load_env_file(API_ENV_FILE)
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY")
    return all(values.get(name, "").strip() for name in required)


def _service_role_client(env: dict[str, str]) -> Client:
    return create_client(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])


def _anon_auth_client(env: dict[str, str]) -> Client:
    return create_client(env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"])


def _create_password_session(admin_client: Client, env: dict[str, str], label: str) -> _SessionContext:
    email = f"rls-{label}-{uuid4().hex}@example.com"
    password = f"T3st!{uuid4().hex}"
    user_response = admin_client.auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": True,
        }
    )
    user_id = UUID(user_response.user.id)

    auth_client = _anon_auth_client(env)
    auth_response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
    assert auth_response.session is not None

    return _SessionContext(
        user_id=user_id,
        access_token=auth_response.session.access_token,
        refresh_token=auth_response.session.refresh_token,
        is_anonymous=False,
    )


def _mint_access_token(
    env: dict[str, str],
    user_id: UUID,
    *,
    email: str,
    is_anonymous: bool,
) -> str:
    now = datetime.now(timezone.utc)
    app_metadata = {"provider": "anonymous", "providers": ["anonymous"], "is_anonymous": is_anonymous}
    claims = {
        "aud": "authenticated",
        "iss": f"{env['SUPABASE_URL']}/auth/v1",
        "sub": str(user_id),
        "email": email,
        "phone": "",
        "role": "authenticated",
        "aal": "aal1",
        "amr": [{"method": "anonymous", "timestamp": int(now.timestamp())}],
        "app_metadata": app_metadata,
        "user_metadata": {},
        "is_anonymous": is_anonymous,
        "session_id": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(claims, env["SUPABASE_JWT_SECRET"], algorithm="HS256")


def _create_anonymous_session_with_fallback(
    admin_client: Client | None,
    env: dict[str, str],
    label: str,
) -> _SessionContext:
    auth_client = _anon_auth_client(env)
    try:
        auth_response = auth_client.auth.sign_in_anonymously()
    except AuthApiError as exc:
        if "Anonymous sign-ins are disabled" not in str(exc):
            raise
        if admin_client is None:
            raise
        email = f"rls-anon-{label}-{uuid4().hex}@example.com"
        user_response = admin_client.auth.admin.create_user(
            {
                "email": email,
                "password": f"T3st!{uuid4().hex}",
                "email_confirm": True,
                "app_metadata": {
                    "provider": "anonymous",
                    "providers": ["anonymous"],
                    "is_anonymous": True,
                },
            }
        )
        user_id = UUID(user_response.user.id)
        return _SessionContext(
            user_id=user_id,
            access_token=_mint_access_token(env, user_id, email=email, is_anonymous=True),
            refresh_token=None,
            is_anonymous=True,
            issued_via_fallback_jwt=True,
        )

    assert auth_response.user is not None
    assert auth_response.session is not None

    return _SessionContext(
        user_id=UUID(auth_response.user.id),
        access_token=auth_response.session.access_token,
        refresh_token=auth_response.session.refresh_token,
        is_anonymous=True,
        issued_via_fallback_jwt=False,
    )


def _rest_select(
    env: dict[str, str],
    access_token: str,
    table_name: str,
    *,
    select: str = "id",
    **filters: str,
) -> list[dict[str, Any]]:
    headers = {
        "apikey": env["SUPABASE_ANON_KEY"],
        "Authorization": f"Bearer {access_token}",
    }
    response = httpx.get(
        f"{env['SUPABASE_URL']}/rest/v1/{table_name}",
        headers=headers,
        params={"select": select, **filters},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    assert isinstance(payload, list)
    return payload


def test_rls_isolation_live_supabase_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    env = _load_env_file(API_ENV_FILE)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    ask_session_repo = AskSessionRepository()
    ask_message_repo = AskMessageRepository()
    dashboard_repo = DashboardRepository()
    widget_repo = WidgetRepository()
    insight_repo = InsightRepository()
    anomaly_repo = AnomalyRepository()
    admin_client = _service_role_client(env)

    created_user_ids: list[UUID] = []

    try:
        user_a = _create_password_session(admin_client, env, "user-a")
        user_b = _create_password_session(admin_client, env, "user-b")
        anonymous_a = _create_anonymous_session_with_fallback(admin_client, env, "a")
        anonymous_b = _create_anonymous_session_with_fallback(admin_client, env, "b")
        created_user_ids.extend([user_a.user_id, user_b.user_id, anonymous_a.user_id, anonymous_b.user_id])

        workspace_a = workspace_repo.create(
            user_a.user_id,
            WorkspaceCreate(name="RLS User A Private", slug=f"rls-user-a-{uuid4().hex[:8]}"),
        )
        workspace_b = workspace_repo.create(
            user_b.user_id,
            WorkspaceCreate(name="RLS User B Private", slug=f"rls-user-b-{uuid4().hex[:8]}"),
        )
        demo_workspace = workspace_repo.create(
            user_a.user_id,
            WorkspaceCreate(name="Demo Workspace", slug="demo"),
        )
        anonymous_workspace = workspace_repo.create(
            anonymous_b.user_id,
            WorkspaceCreate(
                name="Anonymous Private Workspace",
                slug=f"anon-private-{uuid4().hex[:8]}",
                is_anonymous=True,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            ),
        )

        dataset_a = dataset_repo.create(
            workspace_a.id,
            DatasetCreate(
                created_by=user_a.user_id,
                name="User A Dataset",
                storage_path=f"datasets/{workspace_a.id}/user-a.csv",
            ),
        )
        dataset_b = dataset_repo.create(
            workspace_b.id,
            DatasetCreate(
                created_by=user_b.user_id,
                name="User B Dataset",
                storage_path=f"datasets/{workspace_b.id}/user-b.csv",
            ),
        )
        anonymous_dataset = dataset_repo.create(
            anonymous_workspace.id,
            DatasetCreate(
                created_by=anonymous_b.user_id,
                name="Anonymous Private Dataset",
                storage_path=f"datasets/{anonymous_workspace.id}/anon-b.csv",
            ),
        )

        existing_demo_dataset = dataset_repo.get_demo_dataset()
        demo_dataset = existing_demo_dataset or dataset_repo.create(
            demo_workspace.id,
            DatasetCreate(
                created_by=user_a.user_id,
                name="Seeded Demo Dataset",
                source_type="demo_seed",
                storage_path=f"datasets/{demo_workspace.id}/demo-seed.csv",
            ),
        )

        ask_session = ask_session_repo.create(
            workspace_a.id,
            AskSessionCreate(
                created_by=user_a.user_id,
                dataset_id=dataset_a.id,
                title="User A Session",
            ),
        )
        ask_message = ask_message_repo.create(
            workspace_a.id,
            AskMessageCreate(
                session_id=ask_session.id,
                role="user",
                content="Show revenue",
            ),
        )
        dashboard = dashboard_repo.create(
            workspace_a.id,
            DashboardCreate(
                created_by=user_a.user_id,
                name="User A Dashboard",
            ),
        )
        widget = widget_repo.create(
            workspace_a.id,
            WidgetCreate(
                dashboard_id=dashboard.id,
                dataset_id=dataset_a.id,
                title="Revenue Widget",
                widget_type="table",
            ),
        )
        insight = insight_repo.create(
            workspace_a.id,
            InsightCreate(
                dataset_id=dataset_a.id,
                title="Revenue Insight",
                body="Body",
                insight_type="summary",
            ),
        )
        anomaly = anomaly_repo.create(
            workspace_a.id,
            AnomalyCreate(
                dataset_id=dataset_a.id,
                detector_type="zscore",
            ),
        )

        owner_visibility_cases = [
            ("datasets", dataset_a.id, user_a.access_token),
            ("datasets", dataset_b.id, user_b.access_token),
            ("ask_messages", ask_message.id, user_a.access_token),
            ("widgets", widget.id, user_a.access_token),
            ("insights", insight.id, user_a.access_token),
            ("anomalies", anomaly.id, user_a.access_token),
            ("workspaces", anonymous_workspace.id, anonymous_b.access_token),
            ("datasets", anonymous_dataset.id, anonymous_b.access_token),
        ]
        for table_name, record_id, owner_token in owner_visibility_cases:
            rows = _rest_select(env, owner_token, table_name, id=f"eq.{record_id}")
            assert len(rows) == 1, f"owner should be able to read {table_name} record {record_id}"

        cross_user_isolation_cases = [
            ("datasets", dataset_b.id, user_a.access_token),
            ("datasets", dataset_a.id, user_b.access_token),
            ("ask_messages", ask_message.id, user_b.access_token),
            ("widgets", widget.id, user_b.access_token),
            ("insights", insight.id, user_b.access_token),
            ("anomalies", anomaly.id, user_b.access_token),
        ]
        for table_name, record_id, foreign_token in cross_user_isolation_cases:
            rows = _rest_select(env, foreign_token, table_name, id=f"eq.{record_id}")
            assert rows == [], f"non-owner should not read {table_name} record {record_id}"

        demo_rows = _rest_select(env, anonymous_a.access_token, "datasets", id=f"eq.{demo_dataset.id}")
        assert len(demo_rows) == 1, "anonymous user should read the public demo dataset"

        anonymous_isolation_cases = [
            ("workspaces", anonymous_workspace.id, anonymous_a.access_token),
            ("datasets", anonymous_dataset.id, anonymous_a.access_token),
        ]
        for table_name, record_id, foreign_token in anonymous_isolation_cases:
            rows = _rest_select(env, foreign_token, table_name, id=f"eq.{record_id}")
            assert rows == [], f"anonymous non-owner should not read {table_name} record {record_id}"
    finally:
        for user_id in reversed(created_user_ids):
            admin_client.auth.admin.delete_user(str(user_id))
