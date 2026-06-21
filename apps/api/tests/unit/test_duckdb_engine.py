from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import polars as pl
import pytest

from app.analytics.duckdb_engine import execute_dataset_query
from app.core.config import Settings
from app.core.errors import QueryCompilationError, ValidationError
from app.datasets.storage_service import DatasetStoragePaths
from app.db.models import Dataset


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
        assert user_id == self._dataset.created_by
        assert dataset_id == self._dataset.id
        base = f"users/{user_id}/datasets/{dataset_id}"
        return DatasetStoragePaths(
            raw_csv=f"{base}/raw.csv",
            normalized_parquet=f"{base}/normalized.parquet",
            profile_json=f"{base}/profile.json",
            preview_json=f"{base}/preview.json",
        )

    def download_bytes(self, path: str) -> bytes:
        expected = self.build_paths(self._dataset.created_by, self._dataset.id).normalized_parquet
        assert path == expected
        return self._parquet_path.read_bytes()


def _build_dataset() -> Dataset:
    now = datetime.now(timezone.utc)
    workspace_id = uuid4()
    return Dataset(
        id=uuid4(),
        workspace_id=workspace_id,
        created_by=uuid4(),
        name="Test Dataset",
        description=None,
        source_type="upload",
        storage_bucket="readout-datasets",
        storage_path=f"users/{workspace_id}/datasets/raw.csv",
        file_size_bytes=0,
        row_count=0,
        created_at=now,
        updated_at=now,
    )


def _settings(*, max_rows: int = 500, timeout_seconds: int = 10) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_RESULT_ROWS=max_rows,
        QUERY_TIMEOUT_SECONDS=timeout_seconds,
    )


def test_execute_dataset_query_returns_expected_rows(tmp_path: Path) -> None:
    dataset = _build_dataset()
    parquet_path = tmp_path / "dataset.parquet"
    pl.DataFrame(
        {
            "order_id": [1, 2, 3],
            "revenue": [10, 20, 30],
        }
    ).write_parquet(parquet_path)

    result = execute_dataset_query(
        dataset.workspace_id,
        dataset.id,
        "SELECT order_id, revenue FROM dataset WHERE revenue > ? ORDER BY revenue",
        [15],
        settings=_settings(),
        dataset_repository=_FakeDatasetRepository(dataset),
        storage_service=_FakeStorageService(dataset, parquet_path),
    )

    assert result.rows == [
        {"order_id": 2, "revenue": 20},
        {"order_id": 3, "revenue": 30},
    ]
    assert [column.name for column in result.columns] == ["order_id", "revenue"]
    assert result.truncated is False


def test_execute_dataset_query_caps_rows_at_max_result_rows(tmp_path: Path) -> None:
    dataset = _build_dataset()
    parquet_path = tmp_path / "many_rows.parquet"
    pl.DataFrame({"value": list(range(20))}).write_parquet(parquet_path)

    result = execute_dataset_query(
        dataset.workspace_id,
        dataset.id,
        "SELECT value FROM dataset ORDER BY value",
        settings=_settings(max_rows=5),
        dataset_repository=_FakeDatasetRepository(dataset),
        storage_service=_FakeStorageService(dataset, parquet_path),
    )

    assert result.rows == [{"value": 0}, {"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}]
    assert result.truncated is True


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM dataset DrOp   TABLE widgets",
        "SELECT * FROM dataset AtTaCh   'other.duckdb' AS extra_db",
    ],
)
def test_execute_dataset_query_rejects_malicious_strings(tmp_path: Path, sql: str) -> None:
    dataset = _build_dataset()
    parquet_path = tmp_path / "safe.parquet"
    pl.DataFrame({"value": [1]}).write_parquet(parquet_path)

    with pytest.raises(QueryCompilationError, match="forbidden|single read-only"):
        execute_dataset_query(
            dataset.workspace_id,
            dataset.id,
            sql,
            settings=_settings(),
            dataset_repository=_FakeDatasetRepository(dataset),
            storage_service=_FakeStorageService(dataset, parquet_path),
        )


def test_execute_dataset_query_times_out_long_running_query(tmp_path: Path) -> None:
    dataset = _build_dataset()
    parquet_path = tmp_path / "large.parquet"
    pl.DataFrame({"value": list(range(2000))}).write_parquet(parquet_path)

    with pytest.raises(ValidationError, match="QUERY_TIMEOUT_SECONDS"):
        execute_dataset_query(
            dataset.workspace_id,
            dataset.id,
            "SELECT SUM(a.value + b.value + c.value) AS total "
            "FROM dataset a CROSS JOIN dataset b CROSS JOIN dataset c",
            settings=_settings(timeout_seconds=1),
            dataset_repository=_FakeDatasetRepository(dataset),
            storage_service=_FakeStorageService(dataset, parquet_path),
        )
