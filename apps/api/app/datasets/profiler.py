"""Polars-only dataset profiling."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import polars as pl

from app.core.config import Settings
from app.datasets.schema_inference import slugify_column_name


@dataclass(slots=True)
class ColumnProfile:
    """Profile metadata for one dataset column."""

    name: str
    display_name: str
    data_type: str
    semantic_role: str | None
    ordinal_position: int
    is_nullable: bool
    sample_values: list[Any]
    missing_percent: float
    unique_count: int
    min_value: Any | None = None
    max_value: Any | None = None


@dataclass(slots=True)
class DatasetProfileSuccess:
    """Successful CSV profiling result."""

    success: bool
    row_count: int
    duplicate_row_percent: float
    quality_score: int
    warnings: list[str]
    columns: list[ColumnProfile]
    preview_rows: list[dict[str, Any]]
    normalized_parquet: bytes

    def to_profile_payload(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "row_count": self.row_count,
            "duplicate_row_percent": self.duplicate_row_percent,
            "quality_score": self.quality_score,
            "warnings": self.warnings,
            "columns": [asdict(column) for column in self.columns],
        }

    def to_preview_payload(self) -> dict[str, Any]:
        return {
            "rows": self.preview_rows,
            "row_count": len(self.preview_rows),
        }


@dataclass(slots=True)
class DatasetProfileFailure:
    """Structured CSV profiling failure."""

    success: bool
    error_code: str
    error_message: str
    warnings: list[str] = field(default_factory=list)


DatasetProfileResult = DatasetProfileSuccess | DatasetProfileFailure

_TEMPORAL_NAME_TOKENS = ("date", "time", "timestamp", "month", "year", "day")
_IDENTIFIER_NAME_TOKENS = ("id", "uuid", "code", "key")
_METRIC_NAME_TOKENS = ("amount", "count", "cost", "price", "qty", "quantity", "rate", "revenue", "score", "total")
_TEMPORAL_DTYPES = {pl.Date, pl.Datetime, pl.Time}
_INTEGER_DTYPES = {
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
}
_FLOAT_DTYPES = {pl.Float32, pl.Float64}


def _estimated_row_cap(settings: Settings) -> int:
    # Uploads are already size-limited upstream; use the same ceiling to derive
    # a row cap assuming roughly 200 bytes per CSV row so inference never scales
    # with an unbounded row count even if rows are very narrow.
    upload_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    return max(1_000, upload_bytes // 200)


def profile_csv_bytes(content: bytes, settings: Settings) -> DatasetProfileResult:
    """Profile a CSV payload with Polars and return structured success/failure."""

    try:
        raw_headers = _parse_raw_headers(content)
        dataframe = pl.read_csv(
            io.BytesIO(content),
            has_header=False,
            skip_rows=1,
            new_columns=[f"column_{index}" for index in range(len(raw_headers))],
            infer_schema_length=min(2_000, _estimated_row_cap(settings)),
            n_rows=_estimated_row_cap(settings),
            ignore_errors=False,
            try_parse_dates=True,
            truncate_ragged_lines=False,
        )
    except Exception as exc:
        return DatasetProfileFailure(
            success=False,
            error_code="malformed_csv",
            error_message=f"CSV parsing failed: {exc}",
        )

    try:
        return _build_success_profile(dataframe, raw_headers)
    except Exception as exc:
        return DatasetProfileFailure(
            success=False,
            error_code="profiling_failed",
            error_message=f"CSV profiling failed: {exc}",
        )


def _parse_raw_headers(content: bytes) -> list[str]:
    decoded = content.decode("utf-8-sig")
    first_line = decoded.splitlines()[0] if decoded.splitlines() else ""
    headers = next(csv.reader([first_line]))
    if not headers:
        raise ValueError("CSV header row is empty")
    return headers


def _build_success_profile(dataframe: pl.DataFrame, raw_headers: list[str]) -> DatasetProfileSuccess:
    existing_names: set[str] = set()
    warnings: list[str] = []
    columns: list[ColumnProfile] = []
    internal_names: list[str] = []

    for ordinal_position, raw_name in enumerate(raw_headers, start=1):
        series = dataframe.get_column(dataframe.columns[ordinal_position - 1])
        internal_name = slugify_column_name(raw_name, existing_names)
        existing_names.add(internal_name)
        internal_names.append(internal_name)

        non_null_series = series.drop_nulls()
        row_count = max(dataframe.height, 1)
        missing_percent = round(((dataframe.height - non_null_series.len()) / row_count) * 100, 2)
        unique_count = non_null_series.n_unique()

        data_type = _infer_data_type(series, unique_count, dataframe.height)
        semantic_role = _infer_semantic_role(raw_name, data_type)
        sample_values = _sample_values(non_null_series)
        min_value, max_value = _min_max(non_null_series, data_type)

        if missing_percent >= 50:
            warnings.append(f"column '{raw_name}' is {missing_percent:.0f}% missing")

        columns.append(
            ColumnProfile(
                name=internal_name,
                display_name=raw_name,
                data_type=data_type,
                semantic_role=semantic_role,
                ordinal_position=ordinal_position,
                is_nullable=series.null_count() > 0,
                sample_values=sample_values,
                missing_percent=missing_percent,
                unique_count=unique_count,
                min_value=min_value,
                max_value=max_value,
            )
        )

    duplicate_row_percent = _duplicate_row_percent(dataframe)
    if duplicate_row_percent >= 10:
        warnings.append(f"dataset has {duplicate_row_percent:.0f}% duplicate rows")

    quality_score = _quality_score(columns, duplicate_row_percent)

    parquet_buffer = io.BytesIO()
    renamed_dataframe = dataframe.rename(dict(zip(dataframe.columns, internal_names, strict=False)))
    renamed_dataframe.write_parquet(parquet_buffer)

    return DatasetProfileSuccess(
        success=True,
        row_count=dataframe.height,
        duplicate_row_percent=duplicate_row_percent,
        quality_score=quality_score,
        warnings=warnings,
        columns=columns,
        preview_rows=_preview_rows(dataframe, raw_headers),
        normalized_parquet=parquet_buffer.getvalue(),
    )


def _infer_data_type(series: pl.Series, unique_count: int, row_count: int) -> str:
    dtype = series.dtype
    if dtype in _TEMPORAL_DTYPES:
        return "date"
    if dtype in _INTEGER_DTYPES or dtype in _FLOAT_DTYPES or dtype == pl.Decimal:
        return "number"
    if dtype == pl.Boolean:
        return "boolean"
    if dtype == pl.String and row_count > 0 and unique_count <= min(50, max(1, row_count // 5)):
        return "category"
    return "string"


def _infer_semantic_role(raw_name: str, data_type: str) -> str:
    lowered = raw_name.lower()
    if any(token in lowered for token in _TEMPORAL_NAME_TOKENS) or data_type == "date":
        return "time"
    if any(token in lowered for token in _IDENTIFIER_NAME_TOKENS):
        return "identifier"
    if data_type == "number" or any(token in lowered for token in _METRIC_NAME_TOKENS):
        return "metric"
    return "dimension"


def _sample_values(series: pl.Series, limit: int = 5) -> list[Any]:
    values = series.unique(maintain_order=True).head(limit).to_list()
    return [_normalize_value(value) for value in values]


def _min_max(series: pl.Series, data_type: str) -> tuple[Any | None, Any | None]:
    if series.len() == 0 or data_type not in {"date", "number"}:
        return None, None
    return _normalize_value(series.min()), _normalize_value(series.max())


def _duplicate_row_percent(dataframe: pl.DataFrame) -> float:
    if dataframe.height == 0:
        return 0.0
    unique_rows = dataframe.unique().height
    duplicate_rows = dataframe.height - unique_rows
    return round((duplicate_rows / dataframe.height) * 100, 2)


def _quality_score(columns: list[ColumnProfile], duplicate_row_percent: float) -> int:
    if not columns:
        return 0

    # Weighting is explicit because downstream product decisions use this score:
    # 50% missing-data health, 30% type-inference confidence, 20% duplicate-row rate.
    average_missing = sum(column.missing_percent for column in columns) / len(columns)
    missing_component = max(0.0, 100.0 - average_missing)

    confident_columns = sum(1 for column in columns if column.data_type != "string")
    type_confidence_component = (confident_columns / len(columns)) * 100

    duplicate_component = max(0.0, 100.0 - duplicate_row_percent)

    score = (
        (missing_component * 0.50)
        + (type_confidence_component * 0.30)
        + (duplicate_component * 0.20)
    )
    return max(0, min(100, round(score)))


def _preview_rows(dataframe: pl.DataFrame, raw_headers: list[str], limit: int = 5) -> list[dict[str, Any]]:
    rows = dataframe.head(limit).to_dicts()
    preview: list[dict[str, Any]] = []
    for row in rows:
        rendered_row: dict[str, Any] = {}
        for index, raw_header in enumerate(raw_headers):
            rendered_row[raw_header] = _normalize_value(row[dataframe.columns[index]])
        preview.append(rendered_row)
    return preview


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
