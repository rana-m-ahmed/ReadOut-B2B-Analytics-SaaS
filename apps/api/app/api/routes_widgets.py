"""Authenticated dashboard-widget pinning and layout routes."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.routes_datasets import _resolve_current_workspace
from app.core.errors import NotFoundError, ValidationError
from app.db.models import DashboardUpdate, Widget, WidgetCreate, WidgetUpdate
from app.db.repositories import (
    AnomalyRepository,
    AskMessageRepository,
    AskSessionRepository,
    DashboardRepository,
    InsightRepository,
    WidgetRepository,
    WorkspaceRepository,
)
from app.security.auth_guard import CurrentUser, get_current_user

router = APIRouter(tags=["widgets"])

ALLOWED_WIDGET_TYPES = {"metric", "table", "bar", "line", "pie", "area", "scatter"}


class WidgetSourceType(StrEnum):
    ASK_MESSAGE = "ask_message"
    INSIGHT = "insight"
    ANOMALY = "anomaly"


class CreateWidgetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dashboard_id: UUID
    source_type: WidgetSourceType
    source_id: UUID
    title: str | None = Field(default=None, min_length=1, max_length=200)
    position: int | None = Field(default=None, ge=0)


class UpdateWidgetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_update(self) -> UpdateWidgetRequest:
        if self.title is None and self.position is None:
            raise ValueError("At least one widget field must be provided")
        return self


class LayoutPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    widget_id: UUID
    position: int = Field(ge=0)


class UpdateDashboardLayoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    widgets: list[LayoutPosition] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_widgets_and_positions(self) -> UpdateDashboardLayoutRequest:
        widget_ids = [item.widget_id for item in self.widgets]
        positions = [item.position for item in self.widgets]
        if len(widget_ids) != len(set(widget_ids)):
            raise ValueError("Layout contains duplicate widget IDs")
        if len(positions) != len(set(positions)):
            raise ValueError("Layout contains duplicate positions")
        return self


class WidgetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    dashboard_id: UUID
    dataset_id: UUID | None
    title: str
    widget_type: str
    query_text: str | None
    config: dict[str, Any]
    position: int
    created_at: str
    updated_at: str


class DashboardLayoutResponse(BaseModel):
    dashboard_id: UUID
    layout: list[LayoutPosition]


class _PinnedPayload(BaseModel):
    chart_payload: dict[str, Any]
    query_plan: dict[str, Any] | None
    dataset_id: UUID | None
    query_text: str | None
    default_title: str


def _to_widget_response(widget: Widget) -> WidgetResponse:
    return WidgetResponse(
        id=widget.id,
        dashboard_id=widget.dashboard_id,
        dataset_id=widget.dataset_id,
        title=widget.title,
        widget_type=widget.widget_type,
        query_text=widget.query_text,
        config=widget.config,
        position=widget.position,
        created_at=widget.created_at.isoformat(),
        updated_at=widget.updated_at.isoformat(),
    )


def _chart_type(chart_payload: dict[str, Any]) -> str:
    chart_type = chart_payload.get("type")
    if chart_type == "donut":
        chart_type = "pie"
    if chart_type not in ALLOWED_WIDGET_TYPES:
        raise ValidationError("Pinned source has an unsupported chart type")
    return str(chart_type)


def _payload_from_container(
    container: dict[str, Any],
    *,
    dataset_id: UUID | None,
    query_text: str | None,
    default_title: str,
) -> _PinnedPayload:
    chart_payload = container.get("chart_payload")
    if not isinstance(chart_payload, dict):
        chart_payload = container.get("chart")
    if not isinstance(chart_payload, dict) and "type" in container and "data" in container:
        chart_payload = container
    if not isinstance(chart_payload, dict):
        raise ValidationError("Pinned source does not contain a chart payload")

    query_plan = container.get("query_plan")
    if not isinstance(query_plan, dict):
        meta = chart_payload.get("meta")
        query_plan = meta.get("intent") if isinstance(meta, dict) else None
    if query_plan is not None and not isinstance(query_plan, dict):
        raise ValidationError("Pinned source contains an invalid query plan")

    return _PinnedPayload(
        chart_payload=chart_payload,
        query_plan=query_plan,
        dataset_id=dataset_id,
        query_text=query_text,
        default_title=default_title,
    )


def _resolve_pinned_payload(
    workspace_id: UUID,
    source_type: WidgetSourceType,
    source_id: UUID,
) -> _PinnedPayload:
    if source_type == WidgetSourceType.ASK_MESSAGE:
        message_repository = AskMessageRepository()
        message = message_repository.get_for_workspace(workspace_id, source_id)
        if message is None or message.role != "assistant":
            raise NotFoundError("Assistant ask message not found")
        session = AskSessionRepository().get_by_id(workspace_id, message.session_id)
        if session is None:
            raise NotFoundError("Ask session not found")
        return _payload_from_container(
            message.chart_spec or {},
            dataset_id=session.dataset_id,
            query_text=message.sql_text,
            default_title=message.content,
        )

    if source_type == WidgetSourceType.INSIGHT:
        insight = InsightRepository().get_by_id(workspace_id, source_id)
        if insight is None:
            raise NotFoundError("Insight not found")
        return _payload_from_container(
            insight.metadata,
            dataset_id=insight.dataset_id,
            query_text=None,
            default_title=insight.title,
        )

    anomaly = AnomalyRepository().get_by_id(workspace_id, source_id)
    if anomaly is None:
        raise NotFoundError("Anomaly not found")
    return _payload_from_container(
        anomaly.anomaly_payload,
        dataset_id=anomaly.dataset_id,
        query_text=None,
        default_title=anomaly.explanation or anomaly.metric_name or "Anomaly",
    )


@router.post("/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    payload: CreateWidgetRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WidgetResponse:
    workspace = _resolve_current_workspace(current_user, WorkspaceRepository())
    dashboard_repository = DashboardRepository()
    widget_repository = WidgetRepository()
    if dashboard_repository.get_by_id(workspace.id, payload.dashboard_id) is None:
        raise NotFoundError("Dashboard not found")

    pinned = _resolve_pinned_payload(workspace.id, payload.source_type, payload.source_id)
    existing = widget_repository.list_for_dashboard(workspace.id, payload.dashboard_id)
    position = payload.position if payload.position is not None else len(existing)
    widget = widget_repository.create(
        workspace.id,
        WidgetCreate(
            dashboard_id=payload.dashboard_id,
            dataset_id=pinned.dataset_id,
            title=payload.title or pinned.default_title,
            widget_type=_chart_type(pinned.chart_payload),
            query_text=pinned.query_text,
            config={
                "chart_payload": pinned.chart_payload,
                "query_plan": pinned.query_plan,
                "source": {"type": payload.source_type.value, "id": str(payload.source_id)},
            },
            position=position,
        ),
    )
    return _to_widget_response(widget)


@router.get("/dashboards/{dashboard_id}/widgets", response_model=list[WidgetResponse])
async def list_dashboard_widgets(
    dashboard_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[WidgetResponse]:
    workspace = _resolve_current_workspace(current_user, WorkspaceRepository())
    dashboard_repository = DashboardRepository()
    if dashboard_repository.get_by_id(workspace.id, dashboard_id) is None:
        raise NotFoundError("Dashboard not found")
    widgets = WidgetRepository().list_for_dashboard(workspace.id, dashboard_id)
    return [_to_widget_response(widget) for widget in sorted(widgets, key=lambda item: item.position)]


@router.patch("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: UUID,
    payload: UpdateWidgetRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> WidgetResponse:
    workspace = _resolve_current_workspace(current_user, WorkspaceRepository())
    widget = WidgetRepository().update_for_workspace(
        workspace.id,
        widget_id,
        WidgetUpdate(title=payload.title, position=payload.position),
    )
    if widget is None:
        raise NotFoundError("Widget not found")
    return _to_widget_response(widget)


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    workspace = _resolve_current_workspace(current_user, WorkspaceRepository())
    widget_repository = WidgetRepository()
    dashboard_repository = DashboardRepository()
    widget = widget_repository.get_for_workspace(workspace.id, widget_id)
    if widget is None or not widget_repository.delete_for_workspace(workspace.id, widget_id):
        raise NotFoundError("Widget not found")
    dashboard = dashboard_repository.get_by_id(workspace.id, widget.dashboard_id)
    if dashboard is not None:
        remaining_layout = [
            item
            for item in dashboard.layout
            if not isinstance(item, dict) or item.get("widget_id") != str(widget_id)
        ]
        dashboard_repository.update(
            workspace.id,
            widget.dashboard_id,
            DashboardUpdate(layout=remaining_layout),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/dashboards/{dashboard_id}/layout", response_model=DashboardLayoutResponse)
async def update_dashboard_layout(
    dashboard_id: UUID,
    payload: UpdateDashboardLayoutRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> DashboardLayoutResponse:
    workspace = _resolve_current_workspace(current_user, WorkspaceRepository())
    dashboard_repository = DashboardRepository()
    widget_repository = WidgetRepository()
    if dashboard_repository.get_by_id(workspace.id, dashboard_id) is None:
        raise NotFoundError("Dashboard not found")

    existing = {
        widget.id: widget
        for widget in widget_repository.list_for_dashboard(workspace.id, dashboard_id)
    }
    if any(item.widget_id not in existing for item in payload.widgets):
        raise NotFoundError("Layout references a widget outside this dashboard")

    layout = [item.model_dump(mode="json") for item in payload.widgets]
    for item in payload.widgets:
        widget_repository.update(
            workspace.id,
            dashboard_id,
            item.widget_id,
            WidgetUpdate(position=item.position),
        )
    dashboard_repository.update(workspace.id, dashboard_id, DashboardUpdate(layout=layout))
    return DashboardLayoutResponse(dashboard_id=dashboard_id, layout=payload.widgets)
