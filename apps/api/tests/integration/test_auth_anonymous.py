from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.db.models import DatasetCreate, Workspace, WorkspaceCreate
from app.security.auth_guard import CurrentUser, resolve_current_user


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


class _FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.workspaces_by_owner: dict[UUID, list[Workspace]] = {}
        self.create_calls = 0

    def list_for_owner(self, owner_user_id: UUID) -> list[Workspace]:
        return list(self.workspaces_by_owner.get(owner_user_id, []))

    def create(self, owner_user_id: UUID, payload: WorkspaceCreate) -> Workspace:
        self.create_calls += 1
        workspace = Workspace(
            id=payload.id or uuid4(),
            owner_user_id=owner_user_id,
            name=payload.name,
            slug=payload.slug,
            is_anonymous=payload.is_anonymous,
            expires_at=payload.expires_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.workspaces_by_owner.setdefault(owner_user_id, []).append(workspace)
        return workspace


@dataclass
class _FakeDemoDataset:
    id: UUID


class _FakeDatasetRepository:
    def __init__(self) -> None:
        self.demo_dataset = _FakeDemoDataset(id=uuid4())

    def get_demo_dataset(self, workspace_slug: str = "demo", source_type: str = "demo_seed"):
        return self.demo_dataset


class _FakeCleanupDatasetRepository:
    def __init__(self) -> None:
        self.datasets_by_workspace: dict[UUID, set[UUID]] = {}

    def create(self, workspace_id: UUID, payload: DatasetCreate) -> _FakeDemoDataset:
        dataset_id = payload.id or uuid4()
        self.datasets_by_workspace.setdefault(workspace_id, set()).add(dataset_id)
        return _FakeDemoDataset(id=dataset_id)

    def get_by_id(self, workspace_id: UUID, dataset_id: UUID) -> _FakeDemoDataset | None:
        if dataset_id not in self.datasets_by_workspace.get(workspace_id, set()):
            return None
        return _FakeDemoDataset(id=dataset_id)

    def delete_for_workspace(self, workspace_id: UUID) -> int:
        deleted = len(self.datasets_by_workspace.get(workspace_id, set()))
        self.datasets_by_workspace.pop(workspace_id, None)
        return deleted


class _FakeCleanupSupabaseClient:
    def __init__(
        self,
        workspace_repository: "_FakeCleanupWorkspaceRepository",
        dataset_repository: _FakeCleanupDatasetRepository,
    ) -> None:
        self._workspaces = workspace_repository
        self._datasets = dataset_repository

    def rpc(self, function_name: str) -> "_FakeCleanupRpc":
        return _FakeCleanupRpc(function_name, self._workspaces, self._datasets)


class _FakeCleanupRpc:
    def __init__(
        self,
        function_name: str,
        workspace_repository: "_FakeCleanupWorkspaceRepository",
        dataset_repository: _FakeCleanupDatasetRepository,
    ) -> None:
        self._function_name = function_name
        self._workspaces = workspace_repository
        self._datasets = dataset_repository

    def execute(self):
        assert self._function_name == "cleanup_expired_anonymous_workspaces"
        deleted_count = self._workspaces.delete_expired(self._datasets)
        return type("RpcResponse", (), {"data": deleted_count})()


class _FakeCleanupWorkspaceRepository(_FakeWorkspaceRepository):
    def __init__(self) -> None:
        super().__init__()
        self._client: _FakeCleanupSupabaseClient | None = None

    def attach_client(self, client: _FakeCleanupSupabaseClient) -> None:
        self._client = client

    def get_by_id(self, owner_user_id: UUID, workspace_id: UUID) -> Workspace | None:
        for workspace in self.workspaces_by_owner.get(owner_user_id, []):
            if workspace.id == workspace_id:
                return workspace
        return None

    def delete(self, owner_user_id: UUID, workspace_id: UUID) -> bool:
        existing = self.workspaces_by_owner.get(owner_user_id, [])
        remaining = [workspace for workspace in existing if workspace.id != workspace_id]
        if len(remaining) == len(existing):
            return False
        self.workspaces_by_owner[owner_user_id] = remaining
        return True

    def delete_expired(self, dataset_repository: _FakeCleanupDatasetRepository) -> int:
        now = datetime.now(timezone.utc)
        deleted_count = 0
        for owner_user_id, workspaces in list(self.workspaces_by_owner.items()):
            remaining: list[Workspace] = []
            for workspace in workspaces:
                if workspace.is_anonymous and workspace.expires_at is not None and workspace.expires_at < now:
                    dataset_repository.delete_for_workspace(workspace.id)
                    deleted_count += 1
                    continue
                remaining.append(workspace)
            self.workspaces_by_owner[owner_user_id] = remaining
        return deleted_count


def _test_settings(secret: str) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET=secret,
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
    )


def _build_token(secret: str, user_id: UUID, *, is_anonymous: bool) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": is_anonymous},
        },
        secret,
        algorithm="HS256",
    )


def _build_test_app(
    secret: str,
    workspace_repository: _FakeWorkspaceRepository,
    dataset_repository: _FakeDatasetRepository,
) -> FastAPI:
    settings = _test_settings(secret)
    app = FastAPI()
    register_exception_handlers(app)

    async def dependency(request: Request) -> CurrentUser:
        return await resolve_current_user(
            request,
            settings,
            workspace_repository,
            dataset_repository,
        )

    @app.get("/me")
    async def me(current_user: CurrentUser = Depends(dependency)) -> dict[str, Any]:
        return current_user.model_dump(mode="json")

    return app


def test_anonymous_jwt_triggers_workspace_auto_creation_and_is_idempotent() -> None:
    secret = "test-secret-key-with-32-byte-minimum"
    user_id = uuid4()
    workspace_repository = _FakeWorkspaceRepository()
    dataset_repository = _FakeDatasetRepository()
    app = _build_test_app(secret, workspace_repository, dataset_repository)
    client = TestClient(app)
    token = _build_token(secret, user_id, is_anonymous=True)

    first_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    second_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert workspace_repository.create_calls == 1
    assert len(workspace_repository.list_for_owner(user_id)) == 1
    assert first_response.json()["is_anonymous"] is True
    assert first_response.json()["workspace_id"] == second_response.json()["workspace_id"]
    assert first_response.json()["demo_dataset_id"] == str(dataset_repository.demo_dataset.id)


def test_real_user_jwt_never_triggers_anonymous_workspace_logic() -> None:
    secret = "test-secret-key-with-32-byte-minimum"
    user_id = uuid4()
    workspace_repository = _FakeWorkspaceRepository()
    dataset_repository = _FakeDatasetRepository()
    app = _build_test_app(secret, workspace_repository, dataset_repository)
    client = TestClient(app)
    token = _build_token(secret, user_id, is_anonymous=False)

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_anonymous"] is False
    assert response.json()["workspace_id"] is None
    assert response.json()["demo_dataset_id"] is None
    assert workspace_repository.create_calls == 0


@pytest.mark.parametrize(
    ("headers", "expected_message"),
    [
        ({}, "Missing Authorization header"),
        ({"Authorization": "Token abc"}, "Invalid Authorization header"),
    ],
)
def test_missing_or_malformed_authorization_header_returns_typed_401(
    headers: dict[str, str],
    expected_message: str,
) -> None:
    secret = "test-secret-key-with-32-byte-minimum"
    app = _build_test_app(secret, _FakeWorkspaceRepository(), _FakeDatasetRepository())
    client = TestClient(app)

    response = client.get("/me", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"error": {"code": "unauthorized", "message": expected_message}}


def test_invalid_expired_and_malformed_subject_tokens_return_typed_401() -> None:
    secret = "test-secret-key-with-32-byte-minimum"
    app = _build_test_app(secret, _FakeWorkspaceRepository(), _FakeDatasetRepository())
    client = TestClient(app)

    invalid_signature_token = _build_token("different-secret-key-with-32-bytes", uuid4(), is_anonymous=True)
    expired_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "app_metadata": {"is_anonymous": True},
        },
        secret,
        algorithm="HS256",
    )
    malformed_subject_token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": True},
        },
        secret,
        algorithm="HS256",
    )

    invalid_response = client.get("/me", headers={"Authorization": f"Bearer {invalid_signature_token}"})
    expired_response = client.get("/me", headers={"Authorization": f"Bearer {expired_token}"})
    malformed_subject_response = client.get("/me", headers={"Authorization": f"Bearer {malformed_subject_token}"})

    assert invalid_response.status_code == 401
    assert invalid_response.json() == {"error": {"code": "unauthorized", "message": "Invalid token"}}
    assert expired_response.status_code == 401
    assert expired_response.json() == {"error": {"code": "unauthorized", "message": "Token expired"}}
    assert malformed_subject_response.status_code == 401
    assert malformed_subject_response.json() == {
        "error": {"code": "unauthorized", "message": "Token subject must be a valid UUID"}
    }


def test_cleanup_function_removes_expired_anonymous_workspace_and_cascades_locally() -> None:
    migration_sql = (MIGRATIONS_DIR / "0003_cleanup.sql").read_text(encoding="utf-8")
    assert "create or replace function cleanup_expired_anonymous_workspaces()" in migration_sql

    user_id = uuid4()
    workspace_repo = _FakeCleanupWorkspaceRepository()
    dataset_repo = _FakeCleanupDatasetRepository()
    supabase = _FakeCleanupSupabaseClient(workspace_repo, dataset_repo)
    workspace_repo.attach_client(supabase)

    workspace = workspace_repo.create(
        user_id,
        WorkspaceCreate(
            name="Expired Anonymous Workspace",
            slug=f"expired-anon-{uuid4().hex[:8]}",
            is_anonymous=True,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ),
    )
    dataset = dataset_repo.create(
        workspace.id,
        DatasetCreate(
            created_by=user_id,
            name="Expired Dataset",
            storage_path=f"datasets/{workspace.id}/expired.csv",
        ),
    )

    rpc_response = supabase.rpc("cleanup_expired_anonymous_workspaces").execute()

    assert int(rpc_response.data) >= 1
    assert workspace_repo.get_by_id(user_id, workspace.id) is None
    assert dataset_repo.get_by_id(workspace.id, dataset.id) is None
