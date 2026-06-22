"""Typed repository layer with explicit scope filters on every method."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from supabase import Client

from app.db.models import (
    Anomaly,
    AnomalyCreate,
    AnomalyUpdate,
    AskMessage,
    AskMessageCreate,
    AskMessageUpdate,
    AskSession,
    AskSessionCreate,
    AskSessionUpdate,
    Dashboard,
    DashboardCreate,
    DashboardUpdate,
    Dataset,
    DatasetColumn,
    DatasetColumnCreate,
    DatasetColumnUpdate,
    DatasetCreate,
    DatasetUpdate,
    Insight,
    InsightCreate,
    InsightUpdate,
    Profile,
    ProfileCreate,
    ProfileUpdate,
    Widget,
    WidgetCreate,
    WidgetUpdate,
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
)
from app.db.supabase_client import get_supabase_client

ModelT = TypeVar("ModelT", bound=BaseModel)


class _RepositoryBase(Generic[ModelT]):
    """Common helpers for typed repository operations."""

    table_name: str
    model_cls: type[ModelT]

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_supabase_client()

    def _table(self):
        return self._client.table(self.table_name)

    def _parse_one(self, payload: dict[str, Any] | None) -> ModelT | None:
        if payload is None:
            return None
        return self.model_cls.model_validate(payload)

    def _parse_many(self, payload: list[dict[str, Any]] | None) -> list[ModelT]:
        if not payload:
            return []
        return [self.model_cls.model_validate(item) for item in payload]

    def _insert(self, payload: BaseModel) -> ModelT:
        response = self._table().insert(payload.model_dump(mode="json", exclude_none=True)).execute()
        return self._parse_many(response.data)[0]

    def _update_by_filters(
        self,
        payload: BaseModel,
        *,
        filters: dict[str, UUID | str],
    ) -> ModelT | None:
        builder = self._table().update(payload.model_dump(mode="json", exclude_none=True))
        for field_name, field_value in filters.items():
            builder = builder.eq(field_name, str(field_value))
        response = builder.execute()
        return self._parse_one((response.data or [None])[0])

    def _select_one(self, *, filters: dict[str, UUID | str]) -> ModelT | None:
        builder = self._table().select("*")
        for field_name, field_value in filters.items():
            builder = builder.eq(field_name, str(field_value))
        response = builder.execute()
        return self._parse_one((response.data or [None])[0])

    def _select_many(self, *, filters: dict[str, UUID | str]) -> list[ModelT]:
        builder = self._table().select("*")
        for field_name, field_value in filters.items():
            builder = builder.eq(field_name, str(field_value))
        response = builder.execute()
        return self._parse_many(response.data)

    def _delete_by_filters(self, *, filters: dict[str, UUID | str]) -> bool:
        record = self._select_one(filters=filters)
        if record is None:
            return False
        builder = self._table().delete()
        for field_name, field_value in filters.items():
            builder = builder.eq(field_name, str(field_value))
        builder.execute()
        return True


class ProfileRepository(_RepositoryBase[Profile]):
    """Typed CRUD repository for profiles."""

    table_name = "profiles"
    model_cls = Profile

    def create(self, user_id: UUID, payload: ProfileCreate) -> Profile:
        response = self._table().insert(
            {
                "id": str(user_id),
                **payload.model_dump(mode="json", exclude_none=True),
            }
        ).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, user_id: UUID) -> Profile | None:
        return self._select_one(filters={"id": user_id})

    def update(self, user_id: UUID, payload: ProfileUpdate) -> Profile | None:
        return self._update_by_filters(payload, filters={"id": user_id})

    def delete(self, user_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": user_id})


class WorkspaceRepository(_RepositoryBase[Workspace]):
    """Typed CRUD repository for workspaces."""

    table_name = "workspaces"
    model_cls = Workspace

    def create(self, owner_user_id: UUID, payload: WorkspaceCreate) -> Workspace:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["owner_user_id"] = str(owner_user_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, owner_user_id: UUID, workspace_id: UUID) -> Workspace | None:
        return self._select_one(filters={"id": workspace_id, "owner_user_id": owner_user_id})

    def list_for_owner(self, owner_user_id: UUID) -> list[Workspace]:
        return self._select_many(filters={"owner_user_id": owner_user_id})

    def update(self, owner_user_id: UUID, workspace_id: UUID, payload: WorkspaceUpdate) -> Workspace | None:
        return self._update_by_filters(payload, filters={"id": workspace_id, "owner_user_id": owner_user_id})

    def delete(self, owner_user_id: UUID, workspace_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": workspace_id, "owner_user_id": owner_user_id})


class DatasetRepository(_RepositoryBase[Dataset]):
    """Typed CRUD repository for datasets."""

    table_name = "datasets"
    model_cls = Dataset

    def create(self, workspace_id: UUID, payload: DatasetCreate) -> Dataset:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["workspace_id"] = str(workspace_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, dataset_id: UUID) -> Dataset | None:
        return self._select_one(filters={"id": dataset_id, "workspace_id": workspace_id})

    def list_for_workspace(self, workspace_id: UUID) -> list[Dataset]:
        return self._select_many(filters={"workspace_id": workspace_id})

    def get_demo_dataset(self, workspace_slug: str = "demo", source_type: str = "demo_seed") -> Dataset | None:
        response = (
            self._table()
            .select("*, workspaces!inner(slug)")
            .eq("source_type", source_type)
            .eq("workspaces.slug", workspace_slug)
            .limit(1)
            .execute()
        )
        payload = (response.data or [None])[0]
        if payload is None:
            return None
        payload.pop("workspaces", None)
        return self.model_cls.model_validate(payload)

    def update(self, workspace_id: UUID, dataset_id: UUID, payload: DatasetUpdate) -> Dataset | None:
        return self._update_by_filters(payload, filters={"id": dataset_id, "workspace_id": workspace_id})

    def delete(self, workspace_id: UUID, dataset_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": dataset_id, "workspace_id": workspace_id})


class DatasetColumnRepository(_RepositoryBase[DatasetColumn]):
    """Typed CRUD repository for dataset columns."""

    table_name = "dataset_columns"
    model_cls = DatasetColumn

    def __init__(self, client: Client | None = None) -> None:
        super().__init__(client=client)
        self._datasets = DatasetRepository(client=self._client)

    def create(self, workspace_id: UUID, payload: DatasetColumnCreate) -> DatasetColumn:
        dataset = self._datasets.get_by_id(workspace_id, payload.dataset_id)
        if dataset is None:
            raise ValueError("dataset_id is not accessible within the provided workspace_id")
        response = self._table().insert(payload.model_dump(mode="json", exclude_none=True)).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, dataset_id: UUID, column_id: UUID) -> DatasetColumn | None:
        dataset = self._datasets.get_by_id(workspace_id, dataset_id)
        if dataset is None:
            return None
        return self._select_one(filters={"id": column_id, "dataset_id": dataset_id})

    def list_for_dataset(self, workspace_id: UUID, dataset_id: UUID) -> list[DatasetColumn]:
        dataset = self._datasets.get_by_id(workspace_id, dataset_id)
        if dataset is None:
            return []
        return self._select_many(filters={"dataset_id": dataset_id})

    def update(
        self,
        workspace_id: UUID,
        dataset_id: UUID,
        column_id: UUID,
        payload: DatasetColumnUpdate,
    ) -> DatasetColumn | None:
        dataset = self._datasets.get_by_id(workspace_id, dataset_id)
        if dataset is None:
            return None
        return self._update_by_filters(payload, filters={"id": column_id, "dataset_id": dataset_id})

    def delete(self, workspace_id: UUID, dataset_id: UUID, column_id: UUID) -> bool:
        dataset = self._datasets.get_by_id(workspace_id, dataset_id)
        if dataset is None:
            return False
        return self._delete_by_filters(filters={"id": column_id, "dataset_id": dataset_id})


class AskSessionRepository(_RepositoryBase[AskSession]):
    """Typed CRUD repository for ask sessions."""

    table_name = "ask_sessions"
    model_cls = AskSession

    def create(self, workspace_id: UUID, payload: AskSessionCreate) -> AskSession:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["workspace_id"] = str(workspace_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, session_id: UUID) -> AskSession | None:
        return self._select_one(filters={"id": session_id, "workspace_id": workspace_id})

    def list_for_workspace(self, workspace_id: UUID) -> list[AskSession]:
        return self._select_many(filters={"workspace_id": workspace_id})

    def update(self, workspace_id: UUID, session_id: UUID, payload: AskSessionUpdate) -> AskSession | None:
        return self._update_by_filters(payload, filters={"id": session_id, "workspace_id": workspace_id})

    def delete(self, workspace_id: UUID, session_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": session_id, "workspace_id": workspace_id})


class AskMessageRepository(_RepositoryBase[AskMessage]):
    """Typed CRUD repository for ask messages."""

    table_name = "ask_messages"
    model_cls = AskMessage

    def __init__(self, client: Client | None = None) -> None:
        super().__init__(client=client)
        self._sessions = AskSessionRepository(client=self._client)

    def create(self, workspace_id: UUID, payload: AskMessageCreate) -> AskMessage:
        session = self._sessions.get_by_id(workspace_id, payload.session_id)
        if session is None:
            raise ValueError("session_id is not accessible within the provided workspace_id")
        response = self._table().insert(payload.model_dump(mode="json", exclude_none=True)).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, session_id: UUID, message_id: UUID) -> AskMessage | None:
        session = self._sessions.get_by_id(workspace_id, session_id)
        if session is None:
            return None
        return self._select_one(filters={"id": message_id, "session_id": session_id})

    def get_for_workspace(self, workspace_id: UUID, message_id: UUID) -> AskMessage | None:
        response = (
            self._table()
            .select("*, ask_sessions!inner(workspace_id)")
            .eq("id", str(message_id))
            .eq("ask_sessions.workspace_id", str(workspace_id))
            .limit(1)
            .execute()
        )
        payload = (response.data or [None])[0]
        if payload is None:
            return None
        payload.pop("ask_sessions", None)
        return self.model_cls.model_validate(payload)

    def list_for_session(self, workspace_id: UUID, session_id: UUID) -> list[AskMessage]:
        session = self._sessions.get_by_id(workspace_id, session_id)
        if session is None:
            return []
        return self._select_many(filters={"session_id": session_id})

    def update(
        self,
        workspace_id: UUID,
        session_id: UUID,
        message_id: UUID,
        payload: AskMessageUpdate,
    ) -> AskMessage | None:
        session = self._sessions.get_by_id(workspace_id, session_id)
        if session is None:
            return None
        return self._update_by_filters(payload, filters={"id": message_id, "session_id": session_id})

    def delete(self, workspace_id: UUID, session_id: UUID, message_id: UUID) -> bool:
        session = self._sessions.get_by_id(workspace_id, session_id)
        if session is None:
            return False
        return self._delete_by_filters(filters={"id": message_id, "session_id": session_id})


class DashboardRepository(_RepositoryBase[Dashboard]):
    """Typed CRUD repository for dashboards."""

    table_name = "dashboards"
    model_cls = Dashboard

    def create(self, workspace_id: UUID, payload: DashboardCreate) -> Dashboard:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["workspace_id"] = str(workspace_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, dashboard_id: UUID) -> Dashboard | None:
        return self._select_one(filters={"id": dashboard_id, "workspace_id": workspace_id})

    def list_for_workspace(self, workspace_id: UUID) -> list[Dashboard]:
        return self._select_many(filters={"workspace_id": workspace_id})

    def update(self, workspace_id: UUID, dashboard_id: UUID, payload: DashboardUpdate) -> Dashboard | None:
        return self._update_by_filters(payload, filters={"id": dashboard_id, "workspace_id": workspace_id})

    def delete(self, workspace_id: UUID, dashboard_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": dashboard_id, "workspace_id": workspace_id})


class WidgetRepository(_RepositoryBase[Widget]):
    """Typed CRUD repository for widgets."""

    table_name = "widgets"
    model_cls = Widget

    def __init__(self, client: Client | None = None) -> None:
        super().__init__(client=client)
        self._dashboards = DashboardRepository(client=self._client)

    def create(self, workspace_id: UUID, payload: WidgetCreate) -> Widget:
        dashboard = self._dashboards.get_by_id(workspace_id, payload.dashboard_id)
        if dashboard is None:
            raise ValueError("dashboard_id is not accessible within the provided workspace_id")
        response = self._table().insert(payload.model_dump(mode="json", exclude_none=True)).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, dashboard_id: UUID, widget_id: UUID) -> Widget | None:
        dashboard = self._dashboards.get_by_id(workspace_id, dashboard_id)
        if dashboard is None:
            return None
        return self._select_one(filters={"id": widget_id, "dashboard_id": dashboard_id})

    def get_for_workspace(self, workspace_id: UUID, widget_id: UUID) -> Widget | None:
        response = (
            self._table()
            .select("*, dashboards!inner(workspace_id)")
            .eq("id", str(widget_id))
            .eq("dashboards.workspace_id", str(workspace_id))
            .limit(1)
            .execute()
        )
        payload = (response.data or [None])[0]
        if payload is None:
            return None
        payload.pop("dashboards", None)
        return self.model_cls.model_validate(payload)

    def list_for_dashboard(self, workspace_id: UUID, dashboard_id: UUID) -> list[Widget]:
        dashboard = self._dashboards.get_by_id(workspace_id, dashboard_id)
        if dashboard is None:
            return []
        return self._select_many(filters={"dashboard_id": dashboard_id})

    def update(
        self,
        workspace_id: UUID,
        dashboard_id: UUID,
        widget_id: UUID,
        payload: WidgetUpdate,
    ) -> Widget | None:
        dashboard = self._dashboards.get_by_id(workspace_id, dashboard_id)
        if dashboard is None:
            return None
        return self._update_by_filters(payload, filters={"id": widget_id, "dashboard_id": dashboard_id})

    def update_for_workspace(
        self,
        workspace_id: UUID,
        widget_id: UUID,
        payload: WidgetUpdate,
    ) -> Widget | None:
        widget = self.get_for_workspace(workspace_id, widget_id)
        if widget is None:
            return None
        return self.update(workspace_id, widget.dashboard_id, widget_id, payload)

    def delete(self, workspace_id: UUID, dashboard_id: UUID, widget_id: UUID) -> bool:
        dashboard = self._dashboards.get_by_id(workspace_id, dashboard_id)
        if dashboard is None:
            return False
        return self._delete_by_filters(filters={"id": widget_id, "dashboard_id": dashboard_id})

    def delete_for_workspace(self, workspace_id: UUID, widget_id: UUID) -> bool:
        widget = self.get_for_workspace(workspace_id, widget_id)
        if widget is None:
            return False
        return self.delete(workspace_id, widget.dashboard_id, widget_id)


class InsightRepository(_RepositoryBase[Insight]):
    """Typed CRUD repository for insights."""

    table_name = "insights"
    model_cls = Insight

    def create(self, workspace_id: UUID, payload: InsightCreate) -> Insight:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["workspace_id"] = str(workspace_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, insight_id: UUID) -> Insight | None:
        return self._select_one(filters={"id": insight_id, "workspace_id": workspace_id})

    def list_for_workspace(self, workspace_id: UUID) -> list[Insight]:
        return self._select_many(filters={"workspace_id": workspace_id})

    def update(self, workspace_id: UUID, insight_id: UUID, payload: InsightUpdate) -> Insight | None:
        return self._update_by_filters(payload, filters={"id": insight_id, "workspace_id": workspace_id})

    def delete(self, workspace_id: UUID, insight_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": insight_id, "workspace_id": workspace_id})


class AnomalyRepository(_RepositoryBase[Anomaly]):
    """Typed CRUD repository for anomalies."""

    table_name = "anomalies"
    model_cls = Anomaly

    def create(self, workspace_id: UUID, payload: AnomalyCreate) -> Anomaly:
        create_payload = payload.model_dump(mode="json", exclude_none=True)
        create_payload["workspace_id"] = str(workspace_id)
        response = self._table().insert(create_payload).execute()
        return self._parse_many(response.data)[0]

    def get_by_id(self, workspace_id: UUID, anomaly_id: UUID) -> Anomaly | None:
        return self._select_one(filters={"id": anomaly_id, "workspace_id": workspace_id})

    def list_for_workspace(self, workspace_id: UUID) -> list[Anomaly]:
        return self._select_many(filters={"workspace_id": workspace_id})

    def update(self, workspace_id: UUID, anomaly_id: UUID, payload: AnomalyUpdate) -> Anomaly | None:
        return self._update_by_filters(payload, filters={"id": anomaly_id, "workspace_id": workspace_id})

    def delete(self, workspace_id: UUID, anomaly_id: UUID) -> bool:
        return self._delete_by_filters(filters={"id": anomaly_id, "workspace_id": workspace_id})
