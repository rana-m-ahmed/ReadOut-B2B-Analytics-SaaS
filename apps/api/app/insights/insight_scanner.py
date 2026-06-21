from __future__ import annotations
from typing import Any
from uuid import UUID

from app.analytics.duckdb_engine import execute_dataset_query
from app.analytics.result_formatter import format_results
from app.db.models import DatasetColumn
from app.insights.schemas import InsightCandidate
from app.core.config import Settings

def _find_column(columns: list[DatasetColumn], possible_names: list[str]) -> DatasetColumn | None:
    for c in columns:
        for p in possible_names:
            if p in c.name.lower():
                return c
    return None

def scan_dataset_insights(
    workspace_id: UUID,
    dataset_id: UUID,
    columns: list[DatasetColumn],
    settings: Settings
) -> list[InsightCandidate]:
    """Runs statistical queries directly against the dataset parquet to generate candidates."""
    
    candidates: list[InsightCandidate] = []
    
    date_col = _find_column(columns, ["date", "time", "timestamp"])
    metric_cols = [c for c in columns if c.semantic_role in ("metric", "id") and c.data_type in ("numeric", "integer", "float")]
    if not metric_cols:
        # Fallback to revenue or units
        metric_cols = [c for c in columns if "revenue" in c.name.lower() or "price" in c.name.lower() or "units" in c.name.lower()]
        
    category_col = _find_column(columns, ["category", "product"])
    region_col = _find_column(columns, ["region", "country", "territory"])
    customer_col = _find_column(columns, ["customer_type", "user_type"])
    channel_col = _find_column(columns, ["channel", "source", "medium"])
    
    metric_name = metric_cols[0].name if metric_cols else "revenue"

    # 1. Month-over-Month Growth
    if date_col:
        try:
            sql = f"""
            WITH monthly AS (
                SELECT 
                    date_trunc('month', {date_col.name}) as mth,
                    SUM({metric_name}) as total
                FROM dataset
                WHERE {date_col.name} IS NOT NULL
                GROUP BY 1
            ),
            compared AS (
                SELECT 
                    mth, 
                    total,
                    lag(total) OVER (ORDER BY mth) as prev_total
                FROM monthly
            )
            SELECT mth, total, prev_total
            FROM compared
            ORDER BY mth DESC
            LIMIT 1
            """
            res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
            if res.rows and res.rows[0]["prev_total"]:
                row = res.rows[0]
                pct = (row["total"] - row["prev_total"]) / row["prev_total"]
                
                # Make chart payload
                chart_sql = f"SELECT date_trunc('month', {date_col.name}) as bucket, SUM({metric_name}) as {metric_name} FROM dataset WHERE {date_col.name} IS NOT NULL GROUP BY 1 ORDER BY 1 DESC LIMIT 6"
                chart_res = execute_dataset_query(workspace_id, dataset_id, chart_sql, settings=settings)
                
                chart_payload = format_results(chart_res, title="MoM Growth", description="Monthly trend", settings=settings, override_chart_type="line")
                
                candidates.append(InsightCandidate(
                    insight_type="mom_growth",
                    metric_name=metric_name,
                    dimension_name=date_col.name,
                    primary_value=row["total"],
                    comparison_value=row["prev_total"],
                    percent_change=pct,
                    chart_payload=chart_payload.model_dump()
                ))
        except Exception as e:
            pass

    # 2. Top Category
    if category_col:
        try:
            sql = f"""
            SELECT {category_col.name} as cat, SUM({metric_name}) as total
            FROM dataset
            WHERE {category_col.name} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 5
            """
            res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
            if res.rows:
                top = res.rows[0]
                chart_payload = format_results(res, title="Top Category", description="Top 5 categories", settings=settings, override_chart_type="bar")
                candidates.append(InsightCandidate(
                    insight_type="top_category",
                    metric_name=metric_name,
                    dimension_name=category_col.name,
                    primary_value=top["total"],
                    comparison_value=top["cat"],
                    percent_change=None,
                    chart_payload=chart_payload.model_dump()
                ))
        except Exception:
            pass

    # 3. New vs Returning Customer Mix
    if customer_col:
        try:
            sql = f"""
            SELECT {customer_col.name} as type, SUM({metric_name}) as total
            FROM dataset
            WHERE {customer_col.name} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            """
            res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
            if res.rows:
                chart_payload = format_results(res, title="Customer Mix", description="New vs Returning", settings=settings, override_chart_type="donut")
                candidates.append(InsightCandidate(
                    insight_type="customer_mix",
                    metric_name=metric_name,
                    dimension_name=customer_col.name,
                    primary_value=res.rows[0]["total"],
                    comparison_value=res.rows[0]["type"],
                    chart_payload=chart_payload.model_dump()
                ))
        except Exception:
            pass

    # 4. Region Contribution
    if region_col:
        try:
            sql = f"""
            SELECT {region_col.name} as region, SUM({metric_name}) as total
            FROM dataset
            WHERE {region_col.name} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 5
            """
            res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
            if res.rows:
                chart_payload = format_results(res, title="Region Contribution", description="Top regions", settings=settings, override_chart_type="bar")
                candidates.append(InsightCandidate(
                    insight_type="region_contribution",
                    metric_name=metric_name,
                    dimension_name=region_col.name,
                    primary_value=res.rows[0]["total"],
                    comparison_value=res.rows[0]["region"],
                    chart_payload=chart_payload.model_dump()
                ))
        except Exception:
            pass
            
    # 5. Channel Performance
    if channel_col:
        try:
            sql = f"""
            SELECT {channel_col.name} as channel, SUM({metric_name}) as total
            FROM dataset
            WHERE {channel_col.name} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 5
            """
            res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
            if res.rows:
                chart_payload = format_results(res, title="Channel Performance", description="Top channels", settings=settings, override_chart_type="bar")
                candidates.append(InsightCandidate(
                    insight_type="channel_performance",
                    metric_name=metric_name,
                    dimension_name=channel_col.name,
                    primary_value=res.rows[0]["total"],
                    comparison_value=res.rows[0]["channel"],
                    chart_payload=chart_payload.model_dump()
                ))
        except Exception:
            pass
            
    return candidates
