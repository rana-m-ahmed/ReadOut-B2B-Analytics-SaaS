"""Dataset storage service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from app.db.supabase_client import get_supabase_client

DEFAULT_STORAGE_BUCKET = "readout-datasets"


@dataclass(slots=True, frozen=True)
class DatasetStoragePaths:
    """Artifact paths for a single dataset upload."""

    raw_csv: str
    normalized_parquet: str
    profile_json: str
    preview_json: str


class DatasetStorageService:
    """Uploads dataset artifacts through the shared service-role Supabase client."""

    def __init__(self, bucket_name: str = DEFAULT_STORAGE_BUCKET) -> None:
        self._bucket_name = bucket_name
        self._client = get_supabase_client()

    @property
    def bucket_name(self) -> str:
        return self._bucket_name

    def build_paths(self, user_id: UUID, dataset_id: UUID) -> DatasetStoragePaths:
        base = f"users/{user_id}/datasets/{dataset_id}"
        return DatasetStoragePaths(
            raw_csv=f"{base}/raw.csv",
            normalized_parquet=f"{base}/normalized.parquet",
            profile_json=f"{base}/profile.json",
            preview_json=f"{base}/preview.json",
        )

    def upload_raw_csv(self, user_id: UUID, dataset_id: UUID, content: bytes) -> str:
        path = self.build_paths(user_id, dataset_id).raw_csv
        self._upload_bytes(path, content, "text/csv")
        return path

    def upload_normalized_parquet(self, user_id: UUID, dataset_id: UUID, content: bytes) -> str:
        path = self.build_paths(user_id, dataset_id).normalized_parquet
        self._upload_bytes(path, content, "application/octet-stream")
        return path

    def upload_profile_json(self, user_id: UUID, dataset_id: UUID, payload: dict[str, object]) -> str:
        path = self.build_paths(user_id, dataset_id).profile_json
        self._upload_bytes(path, json.dumps(payload, separators=(",", ":")).encode("utf-8"), "application/json")
        return path

    def upload_preview_json(self, user_id: UUID, dataset_id: UUID, payload: dict[str, object]) -> str:
        path = self.build_paths(user_id, dataset_id).preview_json
        self._upload_bytes(path, json.dumps(payload, separators=(",", ":")).encode("utf-8"), "application/json")
        return path

    def create_signed_upload_url(self, path: str) -> str:
        signed_upload = self._client.storage.from_(self._bucket_name).create_signed_upload_url(path)
        upload_url = signed_upload.get("signed_url") or signed_upload.get("signedUrl")
        if not upload_url:
            raise ValueError("Failed to create signed upload URL")
        return str(upload_url)

    def download_bytes(self, path: str) -> bytes:
        return self._client.storage.from_(self._bucket_name).download(path)

    def remove_dataset_artifacts(self, user_id: UUID, dataset_id: UUID) -> list[dict[str, object]]:
        paths = self.build_paths(user_id, dataset_id)
        return self._client.storage.from_(self._bucket_name).remove(
            [paths.raw_csv, paths.normalized_parquet, paths.profile_json, paths.preview_json]
        )

    def _upload_bytes(self, path: str, content: bytes, content_type: str) -> None:
        bucket = self._client.storage.from_(self._bucket_name)
        try:
            bucket.upload(path, content, {"content-type": content_type, "upsert": "true"})
        except Exception:
            bucket.update(path, content, {"content-type": content_type, "upsert": "true"})
