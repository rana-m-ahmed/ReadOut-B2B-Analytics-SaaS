"""Cross-entry-point persistence checks for chart payload cap enforcement."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import jwt
import polars as pl
import pytest
from fastapi.testclient import TestClient

from app.analytics.duckdb_engine import QueryColumn, QueryResult
from app.analytics.result_formatter import format_results
from app.anomalies.zscore_detector import detect_zscore_anomalies
from app.db.models import (
    AnomalyCreate,
    AskMessageCreate,
    AskSessionCreate,
    DashboardCreate,
    InsightCreate,
    InsightUpdate,
    WorkspaceCreate,
)
from app.db.repositories import (
    AnomalyRepository,
    AskMessageRepository,
    AskSessionRepository,
    DashboardRepository,
    DatasetColumnRepository,
    DatasetRepository,
    InsightRepository,
    JsonPayloadTooLargeError,
    WidgetRepository,
    WorkspaceRepository,
)
from app.insights.schemas import InsightCandidate

API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
DEMO_CSV = Path(__file__).resolve().parents[2] / "scripts" / "demo-sales-orders.csv"
TEST_CAP_KB = 4


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _build_auth_token(secret: str, user_id: UUID) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": False},
        },
        secret,
        algorithm="HS256",
    )


def _json_size_bytes(payload: dict) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def _full_demo_daily_result() -> QueryResult:
    daily = (
        pl.read_csv(DEMO_CSV, try_parse_dates=True)
        .group_by("order_date")
        .agg(pl.col("revenue").sum())
        .sort("order_date")
    )
    return QueryResult(
        columns=[
            QueryColumn(name="bucket", duckdb_type="DATE"),
            QueryColumn(name="revenue", duckdb_type="DOUBLE"),
        ],
        rows=[
            {"bucket": row["order_date"], "revenue": row["revenue"]}
            for row in daily.iter_rows(named=True)
        ],
    )


def test_all_chart_payload_entry_points_are_capped_before_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = _load_env_file(API_ENV_FILE)
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET")
    if not all(env.get(name, "").strip() for name in required):
        pytest.skip("requires populated apps/api/.env with live Supabase credentials")

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-placeholder")
    monkeypatch.setenv("MAX_CHART_PAYLOAD_KB", str(TEST_CAP_KB))

    from app.core.config import get_settings
    from app.db.supabase_client import reset_supabase_client
    from app.main import create_app

    get_settings.cache_clear()
    reset_supabase_client()
    settings = get_settings()

    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    column_repository = DatasetColumnRepository()
    session_repository = AskSessionRepository()
    message_repository = AskMessageRepository()
    dashboard_repository = DashboardRepository()
    widget_repository = WidgetRepository()
    insight_repository = InsightRepository()
    anomaly_repository = AnomalyRepository()
    supabase = workspace_repository._client
    demo_dataset = dataset_repository.get_demo_dataset()
    if demo_dataset is None:
        pytest.skip("requires the seeded public demo dataset")

    result = _full_demo_daily_result()
    query_plan = {
        "intent": "time_series",
        "metric": "revenue",
        "aggregation": "sum",
        "group_by": [],
        "date_range": None,
        "filters": [],
        "sort": None,
        "limit": 500,
        "chart_hint": "line",
    }
    chart = format_results(
        result,
        title="Full demo daily revenue",
        description="Ungrouped daily time series across the full demo dataset",
        settings=settings,
        override_chart_type="line",
        meta={"intent": query_plan},
    ).model_dump()
    assert chart["meta"]["truncated"] is True

    user_id: UUID | None = None
    workspace_id: UUID | None = None
    try:
        try:
            user_response = supabase.auth.admin.create_user(
                {
                    "email": f"payload-hygiene-{uuid4().hex}@example.com",
                    "password": f"T3st!{uuid4().hex}",
                    "email_confirm": True,
                }
            )
        except httpx.ConnectError as exc:
            pytest.skip(f"live Supabase host is unreachable: {exc}")

        user_id = UUID(user_response.user.id)
        workspace = workspace_repository.create(
            user_id,
            WorkspaceCreate(
                name="Payload Hygiene Workspace",
                slug=f"payload-hygiene-{uuid4().hex[:8]}",
            ),
        )
        workspace_id = workspace.id
        session = session_repository.create(
            workspace.id,
            AskSessionCreate(
                dataset_id=demo_dataset.id,
                created_by=user_id,
                title="Oversized payload audit",
            ),
        )
        ask_message = message_repository.create(
            workspace.id,
            AskMessageCreate(
                session_id=session.id,
                role="assistant",
                content="Full daily revenue.",
                sql_text="SELECT order_date, sum(revenue) FROM dataset GROUP BY 1",
                chart_spec=chart,
            ),
        )

        dashboard = dashboard_repository.create(
            workspace.id,
            DashboardCreate(created_by=user_id, name="Payload Hygiene Dashboard"),
        )
        client = TestClient(create_app())
        pin_response = client.post(
            "/widgets",
            json={
                "dashboard_id": str(dashboard.id),
                "source_type": "ask_message",
                "source_id": str(ask_message.id),
            },
            headers={
                "Authorization": (
                    f"Bearer {_build_auth_token(env['SUPABASE_JWT_SECRET'], user_id)}"
                )
            },
        )
        assert pin_response.status_code == 201, pin_response.text
        widget = widget_repository.get_for_workspace(
            workspace.id,
            UUID(pin_response.json()["id"]),
        )
        assert widget is not None

        insight_candidate = InsightCandidate(
            insight_type="daily_trend",
            metric_name="revenue",
            dimension_name="order_date",
            primary_value=result.rows[-1]["revenue"],
            chart_payload=chart,
        )
        insight = insight_repository.create(
            workspace.id,
            InsightCreate(
                dataset_id=demo_dataset.id,
                title="Daily revenue trend",
                body="Daily revenue across the full demo period.",
                insight_type="trend",
                metadata={"chart_payload": insight_candidate.chart_payload},
            ),
        )

        detected_anomalies = detect_zscore_anomalies(
            demo_dataset.workspace_id,
            demo_dataset.id,
            column_repository.list_for_dataset(
                demo_dataset.workspace_id,
                demo_dataset.id,
            ),
            settings,
            threshold=3.0,
        )
        assert detected_anomalies
        detected_anomaly = next(
            item
            for item in detected_anomalies
            if item.chart_payload is not None
            and item.chart_payload["meta"]["truncated"] is True
        )
        anomaly = anomaly_repository.create(
            workspace.id,
            AnomalyCreate(
                dataset_id=demo_dataset.id,
                detector_type="zscore",
                metric_name=detected_anomaly.metric_name,
                explanation=detected_anomaly.explanation,
                anomaly_payload={"chart_payload": detected_anomaly.chart_payload},
            ),
        )

        persisted_payloads = {
            "ask_messages.chart_spec": ask_message.chart_spec,
            "widgets.config": widget.config,
            "insights.metadata": insight.metadata,
            "anomalies.anomaly_payload": anomaly.anomaly_payload,
        }
        for field_name, persisted in persisted_payloads.items():
            assert persisted is not None
            assert _json_size_bytes(persisted) <= TEST_CAP_KB * 1024, field_name
            persisted_chart = (
                persisted
                if field_name == "ask_messages.chart_spec"
                else persisted["chart_payload"]
            )
            assert persisted_chart["meta"]["truncated"] is True

        with pytest.raises(JsonPayloadTooLargeError, match="result_formatter"):
            insight_repository.create(
                workspace.id,
                InsightCreate(
                    dataset_id=demo_dataset.id,
                    title="Bypass attempt",
                    body="This should never reach Supabase.",
                    insight_type="summary",
                    metadata={"chart_payload": {"data": ["x" * (TEST_CAP_KB * 2048)]}},
                ),
            )
        with pytest.raises(JsonPayloadTooLargeError, match="result_formatter"):
            insight_repository.update(
                workspace.id,
                insight.id,
                InsightUpdate(
                    metadata={"chart_payload": {"data": ["x" * (TEST_CAP_KB * 2048)]}}
                ),
            )
    finally:
        if user_id is not None and workspace_id is not None:
            workspace_repository.delete(user_id, workspace_id)
        if user_id is not None:
            supabase.auth.admin.delete_user(str(user_id))
        get_settings.cache_clear()
        reset_supabase_client()
