"""Dataset routes."""

from __future__ import annotations

import io
import json
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, ValidationError
from app.db.models import Dataset, DatasetColumnCreate, DatasetCreate, DatasetUpdate, Workspace
from app.db.repositories import DatasetColumnRepository, DatasetRepository, WorkspaceRepository
from app.datasets.profiler import DatasetProfileFailure, DatasetProfileSuccess, profile_csv_bytes
from app.datasets.storage_service import DatasetStorageService
from app.security.auth_guard import CurrentUser, get_current_user
from app.security.file_guard import sanitize_filename, validate_csv_upload

router = APIRouter(prefix="/datasets", tags=["datasets"])


class UploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    file_size_bytes: int = Field(gt=0)
    description: str | None = None


class UploadUrlResponse(BaseModel):
    dataset_id: UUID
    upload_url: str
    storage_path: str


class DatasetListItem(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    source_type: str
    storage_bucket: str
    storage_path: str
    file_size_bytes: int
    row_count: int
    created_at: str
    updated_at: str


class ProfileColumnResponse(BaseModel):
    name: str
    display_name: str
    data_type: str
    semantic_role: str
    missing_percent: float
    unique_count: int
    sample_values: list[Any]
    min_value: Any | None = None
    max_value: Any | None = None


class DatasetProfileResponse(BaseModel):
    dataset_id: UUID
    row_count: int
    quality_score: int
    warnings: list[str]
    columns: list[ProfileColumnResponse]


class DatasetSchemaColumnResponse(BaseModel):
    name: str
    display_name: str
    data_type: str
    semantic_role: str | None
    missing_percent: float


class DatasetSchemaResponse(BaseModel):
    dataset_id: UUID
    columns: list[DatasetSchemaColumnResponse]


def _resolve_current_workspace(
    current_user: CurrentUser,
    workspace_repository: WorkspaceRepository,
) -> Workspace:
    if current_user.workspace_id is not None:
        workspace = workspace_repository.get_by_id(current_user.user_id, current_user.workspace_id)
        if workspace is not None:
            return workspace

    workspaces = workspace_repository.list_for_owner(current_user.user_id)
    if not workspaces:
        raise NotFoundError("No workspace found for current user")
    return workspaces[0]


def _get_dataset_for_current_workspace(
    dataset_id: UUID,
    current_user: CurrentUser,
    workspace_repository: WorkspaceRepository,
    dataset_repository: DatasetRepository,
) -> tuple[Workspace, Dataset]:
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    dataset = dataset_repository.get_by_id(workspace.id, dataset_id)
    if dataset is None:
        raise NotFoundError("Dataset not found")
    return workspace, dataset


def _persist_profile_columns(
    workspace_id: UUID,
    dataset_id: UUID,
    profile: DatasetProfileSuccess,
    dataset_column_repository: DatasetColumnRepository,
) -> None:
    existing_columns = dataset_column_repository.list_for_dataset(workspace_id, dataset_id)
    for existing_column in existing_columns:
        dataset_column_repository.delete(workspace_id, dataset_id, existing_column.id)

    for column in profile.columns:
        dataset_column_repository.create(
            workspace_id,
            DatasetColumnCreate(
                dataset_id=dataset_id,
                name=column.name,
                display_name=column.display_name,
                data_type=column.data_type,
                ordinal_position=column.ordinal_position,
                is_nullable=column.is_nullable,
                semantic_role=column.semantic_role,
                sample_values=column.sample_values,
            ),
        )


def _profile_response(dataset_id: UUID, profile: DatasetProfileSuccess) -> DatasetProfileResponse:
    return DatasetProfileResponse(
        dataset_id=dataset_id,
        row_count=profile.row_count,
        quality_score=profile.quality_score,
        warnings=profile.warnings,
        columns=[
            ProfileColumnResponse(
                name=column.name,
                display_name=column.display_name,
                data_type=column.data_type,
                semantic_role=column.semantic_role or "dimension",
                missing_percent=column.missing_percent,
                unique_count=column.unique_count,
                sample_values=column.sample_values,
                min_value=column.min_value,
                max_value=column.max_value,
            )
            for column in profile.columns
        ],
    )


@router.post("/upload-url", response_model=UploadUrlResponse)
async def create_dataset_upload_url(
    payload: UploadUrlRequest,
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UploadUrlResponse:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    storage_service = DatasetStorageService()
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    max_size_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if payload.file_size_bytes > max_size_bytes:
        raise ValidationError(f"Uploaded file exceeds MAX_UPLOAD_MB ({settings.MAX_UPLOAD_MB} MB)")

    sanitized_filename = sanitize_filename(payload.filename)
    dataset_name = sanitized_filename[:-4] or "upload"
    dataset_id = uuid4()
    storage_path = storage_service.build_paths(current_user.user_id, dataset_id).raw_csv
    dataset = dataset_repository.create(
        workspace.id,
        DatasetCreate(
            id=dataset_id,
            created_by=current_user.user_id,
            name=dataset_name,
            description=payload.description,
            source_type="upload",
            storage_bucket=storage_service.bucket_name,
            storage_path=storage_path,
            file_size_bytes=payload.file_size_bytes,
        ),
    )
    try:
        upload_url = storage_service.create_signed_upload_url(storage_path)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    return UploadUrlResponse(dataset_id=dataset.id, upload_url=upload_url, storage_path=storage_path)


@router.post("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def profile_dataset(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DatasetProfileResponse:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    dataset_column_repository = DatasetColumnRepository()
    storage_service = DatasetStorageService()

    workspace, dataset = _get_dataset_for_current_workspace(
        dataset_id,
        current_user,
        workspace_repository,
        dataset_repository,
    )

    try:
        raw_bytes = storage_service.download_bytes(dataset.storage_path)
    except Exception as exc:
        raise ValidationError("Uploaded raw CSV was not found in storage") from exc
    upload = UploadFile(filename=f"{dataset.name}.csv", file=io.BytesIO(raw_bytes))
    validated = await validate_csv_upload(upload, settings)

    profile_result = profile_csv_bytes(validated.content, settings)
    if isinstance(profile_result, DatasetProfileFailure):
        raise ValidationError(profile_result.error_message)

    storage_service.upload_normalized_parquet(dataset.created_by, dataset.id, profile_result.normalized_parquet)
    storage_service.upload_profile_json(dataset.created_by, dataset.id, profile_result.to_profile_payload())
    storage_service.upload_preview_json(dataset.created_by, dataset.id, profile_result.to_preview_payload())
    updated = dataset_repository.update(
        workspace.id,
        dataset.id,
        DatasetUpdate(row_count=profile_result.row_count),
    )
    dataset = updated or dataset
    _persist_profile_columns(workspace.id, dataset.id, profile_result, dataset_column_repository)
    return _profile_response(dataset.id, profile_result)


@router.get("", response_model=list[DatasetListItem])
async def list_datasets(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[DatasetListItem]:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    datasets = dataset_repository.list_for_workspace(workspace.id)
    return [
        DatasetListItem(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            source_type=dataset.source_type,
            storage_bucket=dataset.storage_bucket,
            storage_path=dataset.storage_path,
            file_size_bytes=dataset.file_size_bytes,
            row_count=dataset.row_count,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
        )
        for dataset in datasets
    ]


@router.get("/{dataset_id}/schema", response_model=DatasetSchemaResponse)
async def get_dataset_schema(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> DatasetSchemaResponse:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    dataset_column_repository = DatasetColumnRepository()
    storage_service = DatasetStorageService()

    workspace, dataset = _get_dataset_for_current_workspace(
        dataset_id,
        current_user,
        workspace_repository,
        dataset_repository,
    )
    columns = dataset_column_repository.list_for_dataset(workspace.id, dataset.id)
    if not columns:
        raise NotFoundError("Dataset schema not found")

    profile_payload = json.loads(
        storage_service.download_bytes(storage_service.build_paths(dataset.created_by, dataset.id).profile_json).decode("utf-8")
    )
    missing_by_name = {
        column_payload["name"]: float(column_payload.get("missing_percent", 0.0))
        for column_payload in profile_payload.get("columns", [])
    }

    return DatasetSchemaResponse(
        dataset_id=dataset.id,
        columns=[
            DatasetSchemaColumnResponse(
                name=column.name,
                display_name=column.display_name or column.name,
                data_type=column.data_type,
                semantic_role=column.semantic_role,
                missing_percent=missing_by_name.get(column.name, 0.0),
            )
            for column in columns
        ],
    )
