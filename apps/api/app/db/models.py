"""Typed database models for repository reads and writes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatabaseModel(BaseModel):
    """Shared database model configuration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Profile(DatabaseModel):
    """Database row for profiles."""

    id: UUID
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ProfileCreate(DatabaseModel):
    """Typed payload for creating a profile."""

    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None


class ProfileUpdate(DatabaseModel):
    """Typed payload for updating a profile."""

    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None


class Workspace(DatabaseModel):
    """Database row for workspaces."""

    id: UUID
    owner_user_id: UUID
    name: str
    slug: str
    is_anonymous: bool = False
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WorkspaceCreate(DatabaseModel):
    """Typed payload for creating a workspace."""

    id: UUID | None = None
    name: str
    slug: str
    is_anonymous: bool = False
    expires_at: datetime | None = None


class WorkspaceUpdate(DatabaseModel):
    """Typed payload for updating a workspace."""

    name: str | None = None
    slug: str | None = None
    is_anonymous: bool | None = None
    expires_at: datetime | None = None


class Dataset(DatabaseModel):
    """Database row for datasets."""

    id: UUID
    workspace_id: UUID
    created_by: UUID
    name: str
    description: str | None = None
    source_type: str = "upload"
    storage_bucket: str = "datasets"
    storage_path: str
    file_size_bytes: int = 0
    row_count: int = 0
    created_at: datetime
    updated_at: datetime


class DatasetCreate(DatabaseModel):
    """Typed payload for creating a dataset."""

    id: UUID | None = None
    created_by: UUID
    name: str
    description: str | None = None
    source_type: str = "upload"
    storage_bucket: str = "datasets"
    storage_path: str
    file_size_bytes: int = 0
    row_count: int = 0


class DatasetUpdate(DatabaseModel):
    """Typed payload for updating a dataset."""

    name: str | None = None
    description: str | None = None
    source_type: str | None = None
    storage_bucket: str | None = None
    storage_path: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None


class DatasetColumn(DatabaseModel):
    """Database row for dataset columns."""

    id: UUID
    dataset_id: UUID
    name: str
    display_name: str | None = None
    data_type: str
    ordinal_position: int
    is_nullable: bool = True
    semantic_role: str | None = None
    sample_values: list[Any] = Field(default_factory=list)
    created_at: datetime


class DatasetColumnCreate(DatabaseModel):
    """Typed payload for creating a dataset column."""

    id: UUID | None = None
    dataset_id: UUID
    name: str
    display_name: str | None = None
    data_type: str
    ordinal_position: int
    is_nullable: bool = True
    semantic_role: str | None = None
    sample_values: list[Any] = Field(default_factory=list)


class DatasetColumnUpdate(DatabaseModel):
    """Typed payload for updating a dataset column."""

    name: str | None = None
    display_name: str | None = None
    data_type: str | None = None
    ordinal_position: int | None = None
    is_nullable: bool | None = None
    semantic_role: str | None = None
    sample_values: list[Any] | None = None


class AskSession(DatabaseModel):
    """Database row for ask sessions."""

    id: UUID
    workspace_id: UUID
    dataset_id: UUID | None = None
    created_by: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class AskSessionCreate(DatabaseModel):
    """Typed payload for creating an ask session."""

    id: UUID | None = None
    dataset_id: UUID | None = None
    created_by: UUID
    title: str | None = None


class AskSessionUpdate(DatabaseModel):
    """Typed payload for updating an ask session."""

    dataset_id: UUID | None = None
    title: str | None = None


class AskMessage(DatabaseModel):
    """Database row for ask messages."""

    id: UUID
    session_id: UUID
    role: str
    content: str
    sql_text: str | None = None
    chart_spec: dict[str, Any] | None = None
    created_at: datetime


class AskMessageCreate(DatabaseModel):
    """Typed payload for creating an ask message."""

    id: UUID | None = None
    session_id: UUID
    role: str
    content: str
    sql_text: str | None = None
    chart_spec: dict[str, Any] | None = None


class AskMessageUpdate(DatabaseModel):
    """Typed payload for updating an ask message."""

    role: str | None = None
    content: str | None = None
    sql_text: str | None = None
    chart_spec: dict[str, Any] | None = None


class Dashboard(DatabaseModel):
    """Database row for dashboards."""

    id: UUID
    workspace_id: UUID
    created_by: UUID
    name: str
    description: str | None = None
    layout: list[Any] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DashboardCreate(DatabaseModel):
    """Typed payload for creating a dashboard."""

    id: UUID | None = None
    created_by: UUID
    name: str
    description: str | None = None
    layout: list[Any] = Field(default_factory=list)


class DashboardUpdate(DatabaseModel):
    """Typed payload for updating a dashboard."""

    name: str | None = None
    description: str | None = None
    layout: list[Any] | None = None


class Widget(DatabaseModel):
    """Database row for widgets."""

    id: UUID
    dashboard_id: UUID
    dataset_id: UUID | None = None
    title: str
    widget_type: str
    query_text: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    position: int = 0
    created_at: datetime
    updated_at: datetime


class WidgetCreate(DatabaseModel):
    """Typed payload for creating a widget."""

    id: UUID | None = None
    dashboard_id: UUID
    dataset_id: UUID | None = None
    title: str
    widget_type: str
    query_text: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    position: int = 0


class WidgetUpdate(DatabaseModel):
    """Typed payload for updating a widget."""

    dataset_id: UUID | None = None
    title: str | None = None
    widget_type: str | None = None
    query_text: str | None = None
    config: dict[str, Any] | None = None
    position: int | None = None


class Insight(DatabaseModel):
    """Database row for insights."""

    id: UUID
    workspace_id: UUID
    dataset_id: UUID | None = None
    title: str
    body: str
    insight_type: str
    severity: str = "info"
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class InsightCreate(DatabaseModel):
    """Typed payload for creating an insight."""

    id: UUID | None = None
    dataset_id: UUID | None = None
    title: str
    body: str
    insight_type: str
    severity: str = "info"
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InsightUpdate(DatabaseModel):
    """Typed payload for updating an insight."""

    dataset_id: UUID | None = None
    title: str | None = None
    body: str | None = None
    insight_type: str | None = None
    severity: str | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None


class Anomaly(DatabaseModel):
    """Database row for anomalies."""

    id: UUID
    workspace_id: UUID
    dataset_id: UUID | None = None
    detector_type: str
    metric_name: str | None = None
    severity: str = "warning"
    explanation: str | None = None
    anomaly_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AnomalyCreate(DatabaseModel):
    """Typed payload for creating an anomaly."""

    id: UUID | None = None
    dataset_id: UUID | None = None
    detector_type: str
    metric_name: str | None = None
    severity: str = "warning"
    explanation: str | None = None
    anomaly_payload: dict[str, Any] = Field(default_factory=dict)


class AnomalyUpdate(DatabaseModel):
    """Typed payload for updating an anomaly."""

    dataset_id: UUID | None = None
    detector_type: str | None = None
    metric_name: str | None = None
    severity: str | None = None
    explanation: str | None = None
    anomaly_payload: dict[str, Any] | None = None
