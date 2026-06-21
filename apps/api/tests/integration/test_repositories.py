from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest

from app.db.models import DatasetCreate, WorkspaceCreate
from app.db.repositories import DatasetRepository, WorkspaceRepository


API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


@dataclass
class _FakeResponse:
    data: list[dict[str, Any]]


class _FakeTable:
    def __init__(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        self._table_name = table_name
        self._rows = rows
        self._filters: dict[str, str] = {}
        self._insert_payload: dict[str, Any] | None = None
        self._update_payload: dict[str, Any] | None = None
        self._mode = "select"

    def select(self, *_args, **_kwargs):
        self._mode = "select"
        return self

    def insert(self, payload: dict[str, Any]):
        self._mode = "insert"
        self._insert_payload = payload
        return self

    def update(self, payload: dict[str, Any]):
        self._mode = "update"
        self._update_payload = payload
        return self

    def delete(self):
        self._mode = "delete"
        return self

    def eq(self, field_name: str, field_value: str):
        self._filters[field_name] = str(field_value)
        return self

    def execute(self) -> _FakeResponse:
        matched_rows = [
            row for row in self._rows if all(str(row.get(key)) == value for key, value in self._filters.items())
        ]
        if self._mode == "insert" and self._insert_payload is not None:
            row = dict(self._insert_payload)
            row.setdefault("id", str(uuid4()))
            row.setdefault("created_at", "2026-06-20T00:00:00Z")
            row.setdefault("updated_at", "2026-06-20T00:00:00Z")
            if self._table_name == "workspaces":
                row.setdefault("is_anonymous", False)
                row.setdefault("expires_at", None)
            if self._table_name == "datasets":
                row.setdefault("description", None)
                row.setdefault("source_type", "upload")
                row.setdefault("storage_bucket", "datasets")
                row.setdefault("file_size_bytes", 0)
                row.setdefault("row_count", 0)
            self._rows.append(row)
            return _FakeResponse([row])
        if self._mode == "update" and self._update_payload is not None:
            for row in matched_rows:
                row.update(self._update_payload)
            return _FakeResponse(matched_rows)
        if self._mode == "delete":
            deleted = list(matched_rows)
            self._rows[:] = [row for row in self._rows if row not in matched_rows]
            return _FakeResponse(deleted)
        return _FakeResponse(matched_rows)


class _FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "workspaces": [],
            "datasets": [],
        }

    def table(self, table_name: str) -> _FakeTable:
        return _FakeTable(table_name, self.tables[table_name])


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
    return bool(values.get("SUPABASE_URL", "").strip()) and bool(
        values.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )


def _create_live_test_user_with_retry(supabase) -> Any:
    last_error: httpx.ConnectError | None = None
    for _attempt in range(3):
        try:
            return supabase.auth.admin.create_user(
                {
                    "email": f"repo-test-{uuid4().hex}@example.com",
                    "password": f"T3st!{uuid4().hex}",
                    "email_confirm": True,
                }
            )
        except httpx.ConnectError as exc:
            last_error = exc
            time.sleep(1)
    raise last_error if last_error is not None else RuntimeError("expected a connect error or user response")


def test_dataset_repository_scopes_reads_with_workspace_filter_fake_client() -> None:
    """Fake-client test: verifies explicit workspace filtering in repository code."""

    fake_client = _FakeSupabaseClient()
    workspaces = WorkspaceRepository(client=fake_client)
    datasets = DatasetRepository(client=fake_client)

    owner_user_id = uuid4()
    workspace_a = workspaces.create(
        owner_user_id,
        WorkspaceCreate(name="Workspace A", slug="workspace-a"),
    )
    workspace_b = workspaces.create(
        owner_user_id,
        WorkspaceCreate(name="Workspace B", slug="workspace-b"),
    )
    created = datasets.create(
        workspace_a.id,
        DatasetCreate(
            created_by=owner_user_id,
            name="Revenue",
            storage_path="datasets/workspace-a/revenue.csv",
        ),
    )

    assert datasets.get_by_id(workspace_a.id, created.id) is not None
    assert datasets.get_by_id(workspace_b.id, created.id) is None


def test_dataset_repository_live_supabase_round_trip_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live-credentials test: real Supabase round trip using the service-role client."""

    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    # The repository layer only needs Supabase config; keep unrelated app config
    # from blocking this live DB validation.
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-placeholder")

    user_id: UUID | None = None
    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    supabase = workspace_repo._client

    try:
        try:
            user_response = _create_live_test_user_with_retry(supabase)
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable with current apps/api/.env: {exc}")
        user_id = UUID(user_response.user.id)

        workspace_a = workspace_repo.create(
            user_id,
            WorkspaceCreate(name="Repo Test A", slug=f"repo-test-a-{uuid4().hex[:8]}"),
        )
        workspace_b = workspace_repo.create(
            user_id,
            WorkspaceCreate(name="Repo Test B", slug=f"repo-test-b-{uuid4().hex[:8]}"),
        )
        dataset = dataset_repo.create(
            workspace_a.id,
            DatasetCreate(
                created_by=user_id,
                name="Dataset A",
                storage_path=f"datasets/{workspace_a.id}/dataset-a.csv",
            ),
        )

        assert dataset_repo.get_by_id(workspace_a.id, dataset.id) is not None
        assert dataset_repo.get_by_id(workspace_b.id, dataset.id) is None
    finally:
        if user_id is not None and supabase is not None:
            supabase.auth.admin.delete_user(str(user_id))
