"""Anomalies routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.db.models import AnomalyCreate, Workspace
from app.db.repositories import (
    AnomalyRepository,
    DatasetColumnRepository,
    DatasetRepository,
    WorkspaceRepository,
)
from app.anomalies.isolation_forest_detector import detect_isolation_forest_anomalies
from app.anomalies.zscore_detector import detect_zscore_anomalies
from app.security.auth_guard import CurrentUser, get_current_user

router = APIRouter(prefix="", tags=["anomalies"])


class AnomalyResponse(BaseModel):
    id: UUID
    dataset_id: UUID | None = None
    detector_type: str
    metric_name: str | None = None
    severity: str
    explanation: str | None = None
    anomaly_payload: dict[str, Any]
    created_at: str


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


@router.get("/datasets/{dataset_id}/anomalies", response_model=list[AnomalyResponse])
async def list_anomalies(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[AnomalyResponse]:
    workspace_repository = WorkspaceRepository()
    anomaly_repository = AnomalyRepository()
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    
    anomalies = anomaly_repository.list_for_workspace(workspace.id)
    
    return [
        AnomalyResponse(
            id=a.id,
            dataset_id=a.dataset_id,
            detector_type=a.detector_type,
            metric_name=a.metric_name,
            severity=a.severity,
            explanation=a.explanation,
            anomaly_payload=a.anomaly_payload,
            created_at=a.created_at.isoformat(),
        )
        for a in anomalies
        if a.dataset_id == dataset_id
    ]


@router.post("/datasets/{dataset_id}/anomalies/scan", response_model=list[AnomalyResponse])
async def scan_anomalies(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> list[AnomalyResponse]:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    column_repository = DatasetColumnRepository()
    anomaly_repository = AnomalyRepository()

    workspace = _resolve_current_workspace(current_user, workspace_repository)
    dataset = dataset_repository.get_by_id(workspace.id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found")

    columns = column_repository.list_for_dataset(workspace.id, dataset_id)
    if not columns:
        raise NotFoundError("No columns found. Ensure the dataset is profiled.")

    # 1. Detect
    z_anomalies = detect_zscore_anomalies(workspace.id, dataset.id, columns, settings)
    if_anomalies = detect_isolation_forest_anomalies(workspace.id, dataset.id, columns, settings)
    
    all_anomalies = z_anomalies + if_anomalies
    
    # 2. Save
    created = []
    for a in all_anomalies:
        anomaly = anomaly_repository.create(
            workspace.id,
            AnomalyCreate(
                dataset_id=dataset.id,
                detector_type=a.detector_type,
                metric_name=a.metric_name,
                severity="high" if abs(a.severity) > 3.0 else "warning",
                explanation=a.explanation,
                anomaly_payload=a.chart_payload or {}
            )
        )
        created.append(anomaly)
        
    return [
        AnomalyResponse(
            id=a.id,
            dataset_id=a.dataset_id,
            detector_type=a.detector_type,
            metric_name=a.metric_name,
            severity=a.severity,
            explanation=a.explanation,
            anomaly_payload=a.anomaly_payload,
            created_at=a.created_at.isoformat(),
        )
        for a in created
    ]


@router.delete("/anomalies/{anomaly_id}", status_code=204)
async def dismiss_anomaly(
    anomaly_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    workspace_repository = WorkspaceRepository()
    anomaly_repository = AnomalyRepository()
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    
    anomaly = anomaly_repository.get_by_id(workspace.id, anomaly_id)
    if not anomaly:
        raise NotFoundError("Anomaly not found")
        
    anomaly_repository.delete(workspace.id, anomaly_id)

