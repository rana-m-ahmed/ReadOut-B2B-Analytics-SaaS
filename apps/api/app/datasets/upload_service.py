"""Dataset upload service."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import UploadFile
from postgrest.exceptions import APIError

from app.core.config import Settings, get_settings
from app.db.models import Dataset, DatasetCreate, DatasetUpdate
from app.datasets.profiler import DatasetProfileFailure, DatasetProfileSuccess, profile_csv_bytes
from app.db.repositories import DatasetRepository
from app.datasets.storage_service import DatasetStoragePaths, DatasetStorageService
from app.security.file_guard import ValidatedCsvUpload, validate_csv_upload


@dataclass(slots=True)
class UploadResult:
    """Result returned by the upload orchestration service."""

    dataset: Dataset
    storage_paths: DatasetStoragePaths
    validated_upload: ValidatedCsvUpload
    status: str
    quality_score: int | None
    profile: DatasetProfileSuccess | None


class DatasetUploadService:
    """Orchestrates CSV validation, persistence, storage, and stub profiling."""

    def __init__(
        self,
        *,
        dataset_repository: DatasetRepository | None = None,
        storage_service: DatasetStorageService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._datasets = dataset_repository or DatasetRepository()
        self._storage = storage_service or DatasetStorageService()
        self._settings = settings or get_settings()

    async def upload_dataset(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        upload: UploadFile,
        description: str | None = None,
        dataset_name: str | None = None,
        source_type: str = "upload",
    ) -> UploadResult:
        validated = await validate_csv_upload(upload, self._settings)
        resolved_dataset_name = dataset_name or validated.sanitized_filename[:-4] or "upload"
        dataset_id = uuid4()
        raw_storage_path = self._storage.build_paths(user_id, dataset_id).raw_csv

        dataset = self._datasets.create(
            workspace_id,
            DatasetCreate(
                id=dataset_id,
                created_by=user_id,
                name=resolved_dataset_name,
                description=description,
                source_type=source_type,
                storage_bucket=self._storage.bucket_name,
                storage_path=raw_storage_path,
                file_size_bytes=validated.size_bytes,
            ),
        )
        self._set_dataset_status(workspace_id, dataset.id, status="processing")

        try:
            raw_path = self._storage.upload_raw_csv(user_id, dataset.id, validated.content)
            profiling_result = profile_csv_bytes(validated.content, self._settings)
            if isinstance(profiling_result, DatasetProfileFailure):
                self._set_dataset_status(
                    workspace_id,
                    dataset.id,
                    status="failed",
                    error_reason=profiling_result.error_message,
                )
                raise ValueError(profiling_result.error_message)
            parquet_path = self._storage.upload_normalized_parquet(
                user_id,
                dataset.id,
                profiling_result.normalized_parquet,
            )
            profile_path = self._storage.upload_profile_json(user_id, dataset.id, profiling_result.to_profile_payload())
            preview_path = self._storage.upload_preview_json(user_id, dataset.id, profiling_result.to_preview_payload())

            updated = self._datasets.update(
                workspace_id,
                dataset.id,
                DatasetUpdate(
                    storage_path=raw_path,
                    storage_bucket=self._storage.bucket_name,
                    row_count=profiling_result.row_count,
                ),
            )
            dataset = updated or dataset
            self._set_dataset_status(workspace_id, dataset.id, status="ready", error_reason=None)
            return UploadResult(
                dataset=dataset,
                storage_paths=DatasetStoragePaths(
                    raw_csv=raw_path,
                    normalized_parquet=parquet_path,
                    profile_json=profile_path,
                    preview_json=preview_path,
                ),
                validated_upload=validated,
                status="ready",
                quality_score=profiling_result.quality_score,
                profile=profiling_result,
            )
        except Exception as exc:
            self._set_dataset_status(workspace_id, dataset.id, status="failed", error_reason=str(exc))
            raise

    def _set_dataset_status(
        self,
        workspace_id: UUID,
        dataset_id: UUID,
        *,
        status: str,
        error_reason: str | None = None,
    ) -> None:
        payload: dict[str, object] = {"status": status, "error_reason": error_reason}
        try:
            (
                self._datasets._table()
                .update(payload)
                .eq("id", str(dataset_id))
                .eq("workspace_id", str(workspace_id))
                .execute()
            )
        except APIError as exc:
            if exc.code not in {"42703", "PGRST204"}:
                raise
