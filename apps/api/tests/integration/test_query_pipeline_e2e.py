from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import tempfile
import shutil

import polars as pl
import pytest

from app.analytics.duckdb_engine import execute_dataset_query
from app.analytics.query_compiler import compile_analytics_intent
from app.analytics.result_formatter import format_results
from app.core.config import Settings
from app.core.errors import QueryCompilationError
from app.datasets.storage_service import DatasetStoragePaths
from app.db.models import Dataset
from app.nlq.intent_validator import DatasetIntentColumn, IntentValidationAccepted, validate_analytics_intent
from app.nlq.schemas import analytics_intent_adapter


class _FakeDatasetRepository:
    def __init__(self, dataset: Dataset) -> None:
        self._dataset = dataset

    def get_by_id(self, workspace_id: UUID, dataset_id: UUID) -> Dataset | None:
        if workspace_id == self._dataset.workspace_id and dataset_id == self._dataset.id:
            return self._dataset
        return None


class _FakeStorageService:
    def __init__(self, dataset: Dataset, parquet_path: Path) -> None:
        self._dataset = dataset
        self._parquet_path = parquet_path

    def build_paths(self, user_id: UUID, dataset_id: UUID) -> DatasetStoragePaths:
        base = f"users/{user_id}/datasets/{dataset_id}"
        return DatasetStoragePaths(
            raw_csv=f"{base}/raw.csv",
            normalized_parquet=f"{base}/normalized.parquet",
            profile_json=f"{base}/profile.json",
            preview_json=f"{base}/preview.json",
        )

    def download_bytes(self, path: str) -> bytes:
        return self._parquet_path.read_bytes()


@pytest.fixture(scope="module")
def e2e_env() -> dict:
    csv_path = Path("apps/api/scripts/demo-sales-orders.csv").resolve()
    df = pl.read_csv(csv_path, try_parse_dates=True)

    temp_dir = Path(tempfile.mkdtemp())
    try:
        parquet_path = temp_dir / "demo.parquet"
        df.write_parquet(parquet_path)
    
        intent_columns = [
            DatasetIntentColumn(name="order_id", data_type="string", unique_count=None),
            DatasetIntentColumn(name="customer_id", data_type="string", unique_count=None),
            DatasetIntentColumn(name="order_date", data_type="date", unique_count=None),
            DatasetIntentColumn(name="product_category", data_type="category", unique_count=None),
            DatasetIntentColumn(name="region", data_type="category", unique_count=None),
            DatasetIntentColumn(name="revenue", data_type="number", unique_count=None),
            DatasetIntentColumn(name="units", data_type="number", unique_count=None),
            DatasetIntentColumn(name="discount_percent", data_type="number", unique_count=None),
        ]

        workspace_id = uuid4()
        dataset = Dataset(
            id=uuid4(),
            workspace_id=workspace_id,
            created_by=uuid4(),
            name="Demo",
            description=None,
            source_type="demo",
            storage_bucket="test",
            storage_path="test",
            file_size_bytes=0,
            row_count=len(df),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        repo = _FakeDatasetRepository(dataset)
        storage = _FakeStorageService(dataset, parquet_path)

        yield {
            "dataset": dataset,
            "repo": repo,
            "storage": storage,
            "columns": intent_columns,
        }
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def _settings(max_payload_kb: float = 50.0) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_CHART_PAYLOAD_KB=max_payload_kb,
        MAX_RESULT_ROWS=5000,
    )


def _run_pipeline(intent_payload: dict, env: dict, settings: Settings) -> dict:
    raw_intent = analytics_intent_adapter.validate_python(intent_payload)
    validated_intent = validate_analytics_intent(raw_intent, env["columns"], settings)
    assert isinstance(validated_intent, IntentValidationAccepted)

    compiled = compile_analytics_intent(validated_intent, settings)

    result = execute_dataset_query(
        env["dataset"].workspace_id,
        env["dataset"].id,
        compiled.sql,
        compiled.params,
        settings=settings,
        dataset_repository=env["repo"],
        storage_service=env["storage"],
    )

    payload = format_results(result, title="Test", description="Desc", settings=settings)
    return payload


def test_e2e_time_series(e2e_env: dict) -> None:
    intent = {
        "intent": "time_series",
        "metric": "revenue",
        "aggregation": "sum",
        "date_range": {"column": "order_date", "start": "2020-01-01", "end": "2030-01-01"},
    }
    payload = _run_pipeline(intent, e2e_env, _settings())
    assert payload.type == "line"
    assert len(payload.data) > 0
    assert payload.meta["truncated"] is False


def test_e2e_grouped_metric(e2e_env: dict) -> None:
    intent = {
        "intent": "grouped_metric",
        "metric": "revenue",
        "aggregation": "sum",
        "group_by": ["region"],
        "date_range": None,
    }
    payload = _run_pipeline(intent, e2e_env, _settings())
    assert payload.type == "bar"
    assert len(payload.data) > 0
    assert payload.meta["truncated"] is False


def test_e2e_single_metric(e2e_env: dict) -> None:
    intent = {
        "intent": "single_metric",
        "metric": "revenue",
        "aggregation": "sum",
        "date_range": None,
    }
    payload = _run_pipeline(intent, e2e_env, _settings())
    assert payload.type == "metric_card"
    assert len(payload.data) == 1
    assert payload.meta["truncated"] is False


def test_e2e_adversarial_sql_injection_filter_value(e2e_env: dict) -> None:
    intent = {
        "intent": "single_metric",
        "metric": "revenue",
        "aggregation": "sum",
        "filters": [{"column": "region", "operator": "eq", "value": "'; DROP TABLE dataset; --"}],
    }
    payload = _run_pipeline(intent, e2e_env, _settings())
    # Should safely return 0 rows/empty data or a 1-row metric card with NULL since filter matches nothing
    assert len(payload.data) == 1
    # Check that it didn't crash


def test_e2e_malicious_keyword_in_engine(e2e_env: dict) -> None:
    # We will invoke the engine directly with a malicious string to make sure engine block still works
    # even with dict-based parameterized arguments
    with pytest.raises(QueryCompilationError, match="forbidden|single read-only"):
        execute_dataset_query(
            e2e_env["dataset"].workspace_id,
            e2e_env["dataset"].id,
            "SELECT * FROM dataset DrOp TABLE dataset",
            {"some_param": 1},
            settings=_settings(),
            dataset_repository=e2e_env["repo"],
            storage_service=e2e_env["storage"],
        )


def test_e2e_payload_capping_triggers_on_large_result(e2e_env: dict) -> None:
    # A full 12 months (or more) of ungrouped daily time series will be large.
    # We set a very small KB limit to guarantee truncation triggers.
    intent = {
        "intent": "time_series",
        "metric": "revenue",
        "aggregation": "sum",
        "date_range": {"column": "order_date", "start": "2020-01-01", "end": "2030-01-01"},
    }
    settings = _settings(max_payload_kb=1.0) # 1 KB limit to force truncation
    payload = _run_pipeline(intent, e2e_env, settings)
    
    assert payload.meta["truncated"] is True
    assert payload.meta["original_row_count"] > len(payload.data)
    assert payload.type == "line"
