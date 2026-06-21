"""Guarded DuckDB execution against a single trusted dataset parquet."""

from __future__ import annotations

import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

import duckdb

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, QueryCompilationError, ValidationError
from app.db.repositories import DatasetRepository
from app.datasets.storage_service import DatasetStorageService

DATASET_VIEW_NAME = "dataset"
_SQL_COMMENT_PATTERN = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)
_DANGEROUS_SQL_PATTERN = re.compile(
    r"\b(drop|delete|insert|update|alter|copy|attach|install|load)\b",
    flags=re.IGNORECASE,
)


@dataclass(slots=True, frozen=True)
class QueryColumn:
    """Column metadata returned from DuckDB."""

    name: str
    duckdb_type: str | None


@dataclass(slots=True, frozen=True)
class QueryResult:
    """Rows plus column metadata, ready for downstream formatting."""

    rows: list[dict[str, Any]]
    columns: list[QueryColumn]
    truncated: bool = False


def execute_dataset_query(
    workspace_id: UUID,
    dataset_id: UUID,
    sql: str,
    parameters: Sequence[Any] | None = None,
    *,
    settings: Settings | None = None,
    dataset_repository: DatasetRepository | None = None,
    storage_service: DatasetStorageService | None = None,
) -> QueryResult:
    """Execute a read-only query against a dataset's trusted normalized parquet."""

    resolved_settings = settings or get_settings()
    repository = dataset_repository or DatasetRepository()
    storage = storage_service or DatasetStorageService()

    _validate_query_sql(sql)
    dataset = repository.get_by_id(workspace_id, dataset_id)
    if dataset is None:
        raise NotFoundError("Dataset not found")

    trusted_path = storage.build_paths(dataset.created_by, dataset.id).normalized_parquet
    parquet_bytes = storage.download_bytes(trusted_path)

    temp_path = _write_temp_parquet(parquet_bytes)
    try:
        return _execute_against_parquet(
            parquet_path=temp_path,
            sql=sql,
            parameters=parameters or (),
            settings=resolved_settings,
        )
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_query_sql(sql: str) -> None:
    normalized = _normalize_sql(sql)
    if not normalized:
        raise QueryCompilationError("Query must not be empty")
    if ";" in normalized:
        raise QueryCompilationError("Query must be a single read-only statement")
    if _DANGEROUS_SQL_PATTERN.search(normalized):
        raise QueryCompilationError("Query contains a forbidden write or extension keyword")
    if not normalized.lower().startswith(("select ", "with ")):
        raise QueryCompilationError("Analytics queries must start with SELECT or WITH")


def _normalize_sql(sql: str) -> str:
    without_comments = _SQL_COMMENT_PATTERN.sub(" ", sql)
    return re.sub(r"\s+", " ", without_comments).strip()


def _write_temp_parquet(parquet_bytes: bytes) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as handle:
        handle.write(parquet_bytes)
        return Path(handle.name)


def _execute_against_parquet(
    *,
    parquet_path: Path,
    sql: str,
    parameters: Sequence[Any],
    settings: Settings,
) -> QueryResult:
    connection = duckdb.connect(
        database=":memory:",
        config={
            "autoload_known_extensions": "false",
            "autoinstall_known_extensions": "false",
        },
    )
    try:
        connection.execute(
            f"CREATE TEMP TABLE {DATASET_VIEW_NAME} AS SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        )
        connection.execute("SET enable_external_access=false")
        limited_sql = f"SELECT * FROM ({sql}) AS __readout_query LIMIT ?"
        bound_parameters = [*parameters, settings.MAX_RESULT_ROWS + 1]
        timer = threading.Timer(float(settings.QUERY_TIMEOUT_SECONDS), connection.interrupt)
        timer.daemon = True
        try:
            timer.start()
            cursor = connection.execute(limited_sql, bound_parameters)
            rows = cursor.fetchall()
        except duckdb.InterruptException as exc:
            raise ValidationError(
                f"Query exceeded QUERY_TIMEOUT_SECONDS ({settings.QUERY_TIMEOUT_SECONDS}s)"
            ) from exc
        finally:
            timer.cancel()

        description = cursor.description or []
        column_names = [column[0] for column in description]
        truncated = len(rows) > settings.MAX_RESULT_ROWS
        limited_rows = rows[: settings.MAX_RESULT_ROWS]
        row_dicts = [dict(zip(column_names, row, strict=False)) for row in limited_rows]
        return QueryResult(
            rows=row_dicts,
            columns=[
                QueryColumn(
                    name=column[0],
                    duckdb_type=(str(column[1]) if len(column) > 1 and column[1] is not None else None),
                )
                for column in description
            ],
            truncated=truncated,
        )
    finally:
        connection.close()
