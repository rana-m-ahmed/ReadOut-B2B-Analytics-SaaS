from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import UploadFile

from app.datasets.storage_service import DatasetStorageService
from app.datasets.upload_service import DatasetUploadService
from app.db.models import WorkspaceCreate
from app.db.repositories import DatasetRepository, WorkspaceRepository


API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


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
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    return all(values.get(name, "").strip() for name in required)


def _upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def test_upload_service_live_storage_round_trip_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials and storage bucket access")

    env = _load_env_file(API_ENV_FILE)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    storage_service = DatasetStorageService()
    upload_service = DatasetUploadService(
        dataset_repository=dataset_repo,
        storage_service=storage_service,
    )
    supabase = workspace_repo._client

    user_id: UUID | None = None
    workspace_id: UUID | None = None
    dataset_id: UUID | None = None
    try:
        try:
            user_response = supabase.auth.admin.create_user(
                {
                    "email": f"upload-test-{uuid4().hex}@example.com",
                    "password": f"T3st!{uuid4().hex}",
                    "email_confirm": True,
                }
            )
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable with current apps/api/.env: {exc}")
        user_id = UUID(user_response.user.id)

        workspace = workspace_repo.create(
            user_id,
            WorkspaceCreate(name="Upload Test Workspace", slug=f"upload-test-{uuid4().hex[:8]}"),
        )
        workspace_id = workspace.id

        result = asyncio.run(
            upload_service.upload_dataset(
                workspace_id=workspace.id,
                user_id=user_id,
                upload=_upload("sales.csv", b"month,revenue\nJan,100\nFeb,120\n"),
                description="Live storage upload test",
            )
        )
        dataset_id = result.dataset.id

        raw_bytes = storage_service.download_bytes(result.storage_paths.raw_csv)
        parquet_bytes = storage_service.download_bytes(result.storage_paths.normalized_parquet)
        profile_payload = json.loads(storage_service.download_bytes(result.storage_paths.profile_json).decode("utf-8"))
        preview_payload = json.loads(storage_service.download_bytes(result.storage_paths.preview_json).decode("utf-8"))

        assert raw_bytes.startswith(b"month,revenue")
        assert len(parquet_bytes) > 0
        assert profile_payload["success"] is True
        assert result.status == "ready"
        assert result.quality_score is not None
        assert profile_payload["row_count"] == 2
        assert preview_payload["row_count"] == 2
        assert result.dataset.storage_bucket == storage_service.bucket_name
        assert result.dataset.storage_path == result.storage_paths.raw_csv
    finally:
        if user_id is not None and dataset_id is not None:
            storage_service.remove_dataset_artifacts(user_id, dataset_id)
        if workspace_id is not None:
            dataset = dataset_repo.get_by_id(workspace_id, dataset_id) if dataset_id is not None else None
            if dataset is not None:
                dataset_repo.delete(workspace_id, dataset_id)
        if user_id is not None and workspace_id is not None:
            workspace_repo.delete(user_id, workspace_id)
        if user_id is not None:
            supabase.auth.admin.delete_user(str(user_id))
