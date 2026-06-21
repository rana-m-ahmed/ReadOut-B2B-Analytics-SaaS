"""Analytics result formatting."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.analytics.chart_recommender import recommend_chart_type
from app.analytics.duckdb_engine import QueryResult
from app.core.config import Settings, get_settings

class ChartPayload(BaseModel):
    type: str
    title: str
    description: str
    x_key: str | None
    y_keys: list[str]
    series: list[str] | None
    data: list[dict[str, Any]]
    meta: dict[str, Any]

def compact_number(num: float) -> str:
    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if abs(num) >= 1_000:
        return f"{num / 1_000:.1f}k"
    if isinstance(num, float) and num.is_integer():
        return str(int(num))
    if isinstance(num, float):
        return f"{num:.2f}"
    return str(num)

def format_value(value: Any, name: str, type_: str) -> str:
    if value is None:
        return "-"
    
    name_lower = name.lower()
    
    if "DATE" in type_ or "TIMESTAMP" in type_:
        if isinstance(value, (date, datetime)):
            return value.strftime("%b %d, %Y")
        return str(value)
        
    if isinstance(value, (int, float)):
        if "revenue" in name_lower or "price" in name_lower or "cost" in name_lower or "amount" in name_lower:
            return f"${compact_number(value)}"
        if "rate" in name_lower or "percent" in name_lower or "ratio" in name_lower or "proportion" in name_lower:
            return f"{value * 100:.1f}%" if value <= 1.0 else f"{value:.1f}%"
        if "count" in name_lower or "qty" in name_lower or "units" in name_lower:
            return str(int(value))
        return compact_number(value)
        
    return str(value)

def _get_payload_size_kb(payload: ChartPayload) -> float:
    # Use default handler for date/datetime
    json_str = payload.model_dump_json()
    return len(json_str.encode("utf-8")) / 1024.0

def _evenly_sample(data: list[dict[str, Any]], target_size: int) -> list[dict[str, Any]]:
    if target_size <= 2:
        return data[:target_size]
    step = (len(data) - 1) / (target_size - 1)
    indices = [int(round(i * step)) for i in range(target_size)]
    return [data[i] for i in indices]

def format_results(
    result: QueryResult,
    title: str,
    description: str,
    settings: Settings | None = None
) -> ChartPayload:
    resolved_settings = settings or get_settings()
    chart_type = recommend_chart_type(result)
    
    x_key = None
    y_keys = []
    
    # Identify x and y keys roughly
    if result.columns:
        # If it's a metric card, no x_key
        if chart_type == "metric_card":
            y_keys = [result.columns[0].name]
        else:
            x_key = result.columns[0].name
            y_keys = [c.name for c in result.columns[1:] if (c.duckdb_type or "").upper() in ("DOUBLE", "INTEGER", "BIGINT", "FLOAT", "DECIMAL", "NUMERIC")]
            
            # If no numerics found, just use everything else
            if not y_keys:
                y_keys = [c.name for c in result.columns[1:]]

    # Format values
    data = []
    for row in result.rows:
        new_row = dict(row)
        for col in result.columns:
            val = new_row.get(col.name)
            if isinstance(val, (date, datetime)):
                new_row[col.name] = val.isoformat()
            new_row[f"formatted_{col.name}"] = format_value(val, col.name, (col.duckdb_type or "").upper())
        data.append(new_row)

    payload = ChartPayload(
        type=chart_type,
        title=title,
        description=description,
        x_key=x_key,
        y_keys=y_keys,
        series=None,
        data=data,
        meta={"truncated": False, "original_row_count": len(data)}
    )
    
    # Cap enforcement
    while len(payload.data) > 2 and _get_payload_size_kb(payload) > resolved_settings.MAX_CHART_PAYLOAD_KB:
        current_size = _get_payload_size_kb(payload)
        ratio = (resolved_settings.MAX_CHART_PAYLOAD_KB / current_size) * 0.9
        target_rows = max(2, int(len(payload.data) * ratio))
        if target_rows >= len(payload.data):
            target_rows = len(payload.data) - 1
            
        if chart_type in ("line", "multi_line", "anomaly_line"):
            payload.data = _evenly_sample(data, target_rows)
        else:
            payload.data = data[:target_rows]
            
        payload.meta["truncated"] = True
        
    return payload
