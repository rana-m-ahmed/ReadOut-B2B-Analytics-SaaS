"""Chart recommendation."""

from __future__ import annotations

from app.analytics.duckdb_engine import QueryResult

def recommend_chart_type(result: QueryResult) -> str:
    """Deterministic lookup mapping result shape to chart type."""
    col_names = [c.name.lower() for c in result.columns]
    
    if "anomaly_value" in col_names and "baseline_value" in col_names:
        return "line_with_highlighted_point"
    if "proportion" in col_names:
        return "donut"
        
    def is_numeric(t: str) -> bool:
        return t in ("DOUBLE", "INTEGER", "BIGINT", "FLOAT", "DECIMAL", "NUMERIC", "HUGEINT", "TINYINT", "SMALLINT", "REAL")
    def is_date(t: str) -> bool:
        return "DATE" in t or "TIMESTAMP" in t

    dates = sum(1 for c in result.columns if is_date((c.duckdb_type or "").upper()))
    numerics = sum(1 for c in result.columns if is_numeric((c.duckdb_type or "").upper()))
    categories = len(result.columns) - dates - numerics

    if dates == 1 and numerics == 1 and categories == 0:
        return "line"
    if dates == 1 and numerics > 1 and categories == 0:
        return "multi_line"
    if categories == 1 and numerics == 1 and dates == 0:
        return "bar"
    if categories == 0 and numerics == 2 and dates == 0:
        return "scatter"
    if dates == 0 and categories == 0 and numerics == 1:
        return "metric_card"
    if dates == 1 and categories >= 1 and numerics >= 1:
        return "stacked_bar"
        
    return "table"
