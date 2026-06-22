"""Insights routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.db.models import InsightCreate, Workspace
from app.db.repositories import (
    DatasetColumnRepository,
    DatasetRepository,
    InsightRepository,
    WorkspaceRepository,
)
from app.insights.insight_ranker import rank_insights
from app.insights.insight_scanner import scan_dataset_insights
from app.insights.insight_writer import write_insights
from app.security.auth_guard import CurrentUser, get_current_user


router = APIRouter(prefix="", tags=["insights"])


class InsightResponse(BaseModel):
    id: UUID
    dataset_id: UUID | None = None
    title: str
    body: str
    insight_type: str
    severity: str
    score: float | None = None
    metadata: dict[str, Any]
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


@router.get("/datasets/{dataset_id}/insights", response_model=list[InsightResponse])
async def list_insights(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[InsightResponse]:
    workspace_repository = WorkspaceRepository()
    insight_repository = InsightRepository()
    workspace = _resolve_current_workspace(current_user, workspace_repository)
    
    # Filter by workspace, then in Python by dataset to reuse the workspace fetch pattern
    insights = insight_repository.list_for_workspace(workspace.id)
    
    return [
        InsightResponse(
            id=i.id,
            dataset_id=i.dataset_id,
            title=i.title,
            body=i.body,
            insight_type=i.insight_type,
            severity=i.severity,
            score=i.score,
            metadata=i.metadata,
            created_at=i.created_at.isoformat(),
        )
        for i in insights
        if i.dataset_id == dataset_id
    ]


@router.post("/datasets/{dataset_id}/insights/generate", response_model=list[InsightResponse])
async def generate_insights(
    dataset_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> list[InsightResponse]:
    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    column_repository = DatasetColumnRepository()
    insight_repository = InsightRepository()

    workspace = _resolve_current_workspace(current_user, workspace_repository)
    dataset = dataset_repository.get_by_id(workspace.id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found")

    columns = column_repository.list_for_dataset(workspace.id, dataset_id)
    if not columns:
        raise NotFoundError("No columns found. Ensure the dataset is profiled.")

    # 1. Scan
    candidates = scan_dataset_insights(workspace.id, dataset.id, columns, settings)
    
    # 2. Rank
    existing = insight_repository.list_for_workspace(workspace.id)
    history_types = {i.insight_type for i in existing if i.dataset_id == dataset.id}
    ranked = rank_insights(candidates, history_types)
    
    # 3. Write
    written = await write_insights(ranked, settings, limit=3)
    
    # Save to DB
    created = []
    for c in written:
        if not c.text:
            continue
        insight = insight_repository.create(
            workspace.id,
            InsightCreate(
                dataset_id=dataset.id,
                title=f"{c.metric_name.replace('_', ' ').title()} Insight",
                body=c.text,
                insight_type=c.insight_type,
                severity="info",
                score=c.score,
                metadata={"chart_payload": c.chart_payload}
            )
        )
        created.append(insight)
        
    return [
        InsightResponse(
            id=i.id,
            dataset_id=i.dataset_id,
            title=i.title,
            body=i.body,
            insight_type=i.insight_type,
            severity=i.severity,
            score=i.score,
            metadata=i.metadata,
            created_at=i.created_at.isoformat(),
        )
        for i in created
    ]
