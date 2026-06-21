from __future__ import annotations
from typing import Any
from uuid import UUID

from app.analytics.duckdb_engine import execute_dataset_query
from app.analytics.result_formatter import format_results
from app.db.models import DatasetColumn
from app.anomalies.schemas import Anomaly
from app.core.config import Settings

def _find_column(columns: list[DatasetColumn], possible_names: list[str]) -> DatasetColumn | None:
    for c in columns:
        for p in possible_names:
            if p in c.name.lower():
                return c
    return None

def detect_zscore_anomalies(
    workspace_id: UUID,
    dataset_id: UUID,
    columns: list[DatasetColumn],
    settings: Settings,
    threshold: float = 3.0
) -> list[Anomaly]:
    """Runs a weekday-aware rolling-mean/stddev z-score detector."""
    
    anomalies: list[Anomaly] = []
    
    date_col = _find_column(columns, ["date", "time", "timestamp"])
    if not date_col:
        return []
        
    metric_cols = [c for c in columns if c.semantic_role in ("metric", "id") and c.data_type in ("numeric", "integer", "float")]
    if not metric_cols:
        metric_cols = [c for c in columns if "revenue" in c.name.lower() or "price" in c.name.lower() or "units" in c.name.lower()]
    
    category_col = _find_column(columns, ["category", "product"])
    region_col = _find_column(columns, ["region", "country", "territory"])
    
    metric_name = metric_cols[0].name if metric_cols else "revenue"
    
    # Run a generic scan for daily revenue
    queries = []
    
    # 1. Total Daily Revenue
    queries.append({
        "type": "daily_metric",
        "dim_col": None,
        "metric": metric_name,
        "sql": f"""
            WITH daily AS (
                SELECT date_trunc('day', {date_col.name}) as d, sum({metric_name}) as val
                FROM dataset
                WHERE {date_col.name} IS NOT NULL
                GROUP BY 1
            ),
            stats AS (
                SELECT d, val,
                       avg(val) OVER w as mean,
                       stddev_samp(val) OVER w as std
                FROM daily
                WINDOW w AS (PARTITION BY dayofweek(d) ORDER BY d ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING)
            )
            SELECT *, (val - mean) / std as z
            FROM stats 
            WHERE std > 0.05 * mean AND abs(val - mean) > 0.2 * mean AND abs((val - mean) / std) >= {threshold}
            ORDER BY abs(z) DESC LIMIT 5
        """
    })
    
    # 2. Revenue by Region
    if region_col:
        queries.append({
            "type": "region_metric",
            "dim_col": region_col.name,
            "metric": metric_name,
            "sql": f"""
                WITH daily AS (
                    SELECT date_trunc('day', {date_col.name}) as d, {region_col.name} as dim, sum({metric_name}) as val
                    FROM dataset
                    WHERE {date_col.name} IS NOT NULL AND {region_col.name} IS NOT NULL
                    GROUP BY 1, 2
                ),
                stats AS (
                    SELECT d, dim, val,
                           avg(val) OVER w as mean,
                           stddev_samp(val) OVER w as std
                    FROM daily
                    WINDOW w AS (PARTITION BY dim, dayofweek(d) ORDER BY d ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING)
                )
                SELECT *, (val - mean) / std as z
                FROM stats 
                WHERE std > 0.05 * mean AND abs(val - mean) > 0.2 * mean AND abs((val - mean) / std) >= {threshold}
            """
        })
        
    # 3. Revenue by Category
    if category_col:
        queries.append({
            "type": "category_metric",
            "dim_col": category_col.name,
            "metric": metric_name,
            "sql": f"""
                WITH daily AS (
                    SELECT date_trunc('day', {date_col.name}) as d, {category_col.name} as dim, sum({metric_name}) as val
                    FROM dataset
                    WHERE {date_col.name} IS NOT NULL AND {category_col.name} IS NOT NULL
                    GROUP BY 1, 2
                ),
                stats AS (
                    SELECT d, dim, val,
                           avg(val) OVER w as mean,
                           stddev_samp(val) OVER w as std
                    FROM daily
                    WINDOW w AS (PARTITION BY dim, dayofweek(d) ORDER BY d ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING)
                )
                SELECT *, (val - mean) / std as z
                FROM stats 
                WHERE std > 0.05 * mean AND abs(val - mean) > 0.2 * mean AND abs((val - mean) / std) >= {threshold}
            """
        })
        
    # 4. Revenue by Region and Category (for the specific seeded anomaly)
    if region_col and category_col:
        queries.append({
            "type": "region_category_metric",
            "dim_col": f"{region_col.name} / {category_col.name}",
            "metric": metric_name,
            "sql": f"""
                WITH daily AS (
                    SELECT date_trunc('day', {date_col.name}) as d, 
                           {region_col.name} || ' / ' || {category_col.name} as dim, 
                           sum({metric_name}) as val
                    FROM dataset
                    WHERE {date_col.name} IS NOT NULL 
                      AND {region_col.name} IS NOT NULL 
                      AND {category_col.name} IS NOT NULL
                    GROUP BY 1, 2
                ),
                stats AS (
                    SELECT d, dim, val,
                           avg(val) OVER w as mean,
                           stddev_samp(val) OVER w as std
                    FROM daily
                    WINDOW w AS (PARTITION BY dim, dayofweek(d) ORDER BY d ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING)
                )
                SELECT *, (val - mean) / std as z
                FROM stats 
                WHERE std > 0.05 * mean AND abs(val - mean) > 0.2 * mean AND abs((val - mean) / std) >= {threshold}
            """
        })
        
    for q in queries:
        try:
            res = execute_dataset_query(workspace_id, dataset_id, q["sql"], settings=settings)
            
            # Noise is already filtered by the WHERE clause
            top_rows = sorted(res.rows, key=lambda r: abs(r["z"]), reverse=True)
            
            for row in top_rows:
                anomalies.append(Anomaly(
                    detector_type="zscore",
                    date=str(row["d"]),
                    metric_name=q["metric"],
                    dimension_name=q["dim_col"],
                    dimension_value=row.get("dim"),
                    actual_value=row["val"],
                    expected_value=row["mean"],
                    severity=row["z"],
                    chart_payload=None
                ))
        except Exception as e:
            pass
            
    # Sort anomalies by absolute severity
    anomalies.sort(key=lambda a: abs(a.severity), reverse=True)
    return anomalies
