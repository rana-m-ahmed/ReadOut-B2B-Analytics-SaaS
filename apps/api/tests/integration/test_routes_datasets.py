from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

from app.db.models import WorkspaceCreate
from app.db.repositories import (
    DatasetColumnRepository,
    DatasetRepository,
    WorkspaceRepository,
)


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
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET")
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


def _upload_to_signed_url(upload_url: str, content: bytes, content_type: str = "text/csv") -> None:
    headers = {"content-type": content_type, "x-upsert": "false"}
    response = httpx.put(upload_url, content=content, headers=headers, timeout=60.0)
    if response.status_code >= 400:
        response = httpx.post(upload_url, content=content, headers=headers, timeout=60.0)
    response.raise_for_status()


def test_routes_datasets_live_round_trip_and_rejections(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    env = _load_env_file(API_ENV_FILE)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    from app.main import create_app

    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    column_repo = DatasetColumnRepository()
    supabase = workspace_repo._client
    app = create_app()
    client = TestClient(app)

    user_id: UUID | None = None
    workspace_id: UUID | None = None
    dataset_id: UUID | None = None
    invalid_dataset_id: UUID | None = None
    try:
        email = f"routes-datasets-{uuid4().hex}@example.com"
        password = f"T3st!{uuid4().hex}"
        try:
            user_response = supabase.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                }
            )
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable with current apps/api/.env: {exc}")
        user_id = UUID(user_response.user.id)
        access_token = _build_auth_token(env, user_id)

        workspace = workspace_repo.create(
            user_id,
            WorkspaceCreate(name="Routes Dataset Workspace", slug=f"routes-datasets-{uuid4().hex[:8]}"),
        )
        workspace_id = workspace.id

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        upload_url_response = client.post(
            "/datasets/upload-url",
            json={
                "filename": "sales.csv",
                "file_size_bytes": len(b"month,revenue\nJan,100\nFeb,120\n"),
                "description": "Route round trip test",
            },
            headers=auth_headers,
        )
        assert upload_url_response.status_code == 200
        upload_url_payload = upload_url_response.json()
        dataset_id = UUID(upload_url_payload["dataset_id"])
        assert upload_url_payload["storage_path"].endswith("/raw.csv")

        _upload_to_signed_url(upload_url_payload["upload_url"], b"month,revenue\nJan,100\nFeb,120\n")

        profile_response = client.post(f"/datasets/{dataset_id}/profile", headers=auth_headers)
        assert profile_response.status_code == 200
        profile_payload = profile_response.json()
        assert profile_payload["dataset_id"] == str(dataset_id)
        assert profile_payload["row_count"] == 2
        assert profile_payload["quality_score"] >= 80
        assert {column["name"] for column in profile_payload["columns"]} == {"month", "revenue"}

        list_response = client.get("/datasets", headers=auth_headers)
        assert list_response.status_code == 200
        list_payload = list_response.json()
        listed_dataset = next(item for item in list_payload if item["id"] == str(dataset_id))
        assert listed_dataset["storage_path"] == upload_url_payload["storage_path"]
        assert listed_dataset["row_count"] == 2

        schema_response = client.get(f"/datasets/{dataset_id}/schema", headers=auth_headers)
        assert schema_response.status_code == 200
        schema_payload = schema_response.json()
        assert schema_payload["dataset_id"] == str(dataset_id)
        assert schema_payload["columns"] == [
            {
                "name": "month",
                "display_name": "month",
                "data_type": "string",
                "semantic_role": "time",
                "missing_percent": 0.0,
            },
            {
                "name": "revenue",
                "display_name": "revenue",
                "data_type": "number",
                "semantic_role": "metric",
                "missing_percent": 0.0,
            },
        ]

        columns = column_repo.list_for_dataset(workspace_id, dataset_id)
        month_column = next(column for column in columns if column.name == "month")
        revenue_column = next(column for column in columns if column.name == "revenue")
        supabase.rpc(
            "activate_dataset_analysis_config",
            {
                "p_dataset_id": str(dataset_id),
                "p_created_by": str(user_id),
                "p_base_version": 0,
                "p_primary_time_column_id": str(month_column.id),
                "p_metrics": [
                    {
                        "column_id": str(revenue_column.id),
                        "label": "Revenue",
                        "aggregation": "sum",
                        "display_format": "number",
                        "position": 0,
                        "is_primary": True,
                    }
                ],
                "p_dimensions": [
                    {
                        "column_id": str(month_column.id),
                        "label": "Month",
                        "position": 0,
                    }
                ],
            },
        ).execute()

        delete_response = client.delete(f"/datasets/{dataset_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        assert dataset_repo.get_by_id(workspace_id, dataset_id) is None

        post_delete_list_response = client.get("/datasets", headers=auth_headers)
        assert post_delete_list_response.status_code == 200
        assert all(item["id"] != str(dataset_id) for item in post_delete_list_response.json())
        dataset_id = None

        oversized_response = client.post(
            "/datasets/upload-url",
            json={
                "filename": "too-big.csv",
                "file_size_bytes": (26 * 1024 * 1024),
            },
            headers=auth_headers,
        )
        assert oversized_response.status_code == 400
        assert oversized_response.json()["error"]["code"] == "validation_error"

        invalid_upload_response = client.post(
            "/datasets/upload-url",
            json={
                "filename": "renamed.csv",
                "file_size_bytes": len(b"MZfake-executable-content"),
            },
            headers=auth_headers,
        )
        assert invalid_upload_response.status_code == 200
        invalid_payload = invalid_upload_response.json()
        invalid_dataset_id = UUID(invalid_payload["dataset_id"])

        _upload_to_signed_url(invalid_payload["upload_url"], b"MZfake-executable-content")
        invalid_profile_response = client.post(f"/datasets/{invalid_dataset_id}/profile", headers=auth_headers)
        assert invalid_profile_response.status_code == 400
        assert invalid_profile_response.json()["error"]["code"] == "validation_error"
    finally:
        if workspace_id is not None:
            for dataset in dataset_repo.list_for_workspace(workspace_id):
                dataset_repo.delete(workspace_id, dataset.id)
        if user_id is not None and workspace_id is not None:
            workspace_repo.delete(user_id, workspace_id)
        if user_id is not None:
            supabase.auth.admin.delete_user(str(user_id))
