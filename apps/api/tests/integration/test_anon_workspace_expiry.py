from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import httpx
import pytest

from app.db.models import DatasetCreate, WorkspaceCreate
from app.db.repositories import DatasetRepository, WorkspaceRepository
from .test_rls_isolation import (
    API_ENV_FILE,
    _create_anonymous_session_with_fallback,
    _has_live_supabase_credentials,
    _load_env_file,
    _rest_select,
    _service_role_client,
)


def test_expired_anonymous_workspace_is_immediately_hidden_by_rls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    env = _load_env_file(API_ENV_FILE)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    admin_client = _service_role_client(env)
    created_user_ids: list[UUID] = []

    try:
        try:
            anonymous_user = _create_anonymous_session_with_fallback(admin_client, env, "expired-owner")
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable: {exc}")
        created_user_ids.append(anonymous_user.user_id)

        expired_workspace = workspace_repo.create(
            anonymous_user.user_id,
            WorkspaceCreate(
                name="Expired Anonymous Workspace",
                slug=f"expired-anon-{uuid4().hex[:8]}",
                is_anonymous=True,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            ),
        )
        expired_dataset = dataset_repo.create(
            expired_workspace.id,
            DatasetCreate(
                created_by=anonymous_user.user_id,
                name="Expired Anonymous Dataset",
                storage_path=f"datasets/{expired_workspace.id}/expired.csv",
            ),
        )

        workspace_rows = _rest_select(
            env,
            anonymous_user.access_token,
            "workspaces",
            id=f"eq.{expired_workspace.id}",
        )
        dataset_rows = _rest_select(
            env,
            anonymous_user.access_token,
            "datasets",
            id=f"eq.{expired_dataset.id}",
        )

        assert workspace_rows == []
        assert dataset_rows == []
    finally:
        for user_id in reversed(created_user_ids):
            admin_client.auth.admin.delete_user(str(user_id))
