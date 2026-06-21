from __future__ import annotations

from datetime import date

from app.analytics.duckdb_engine import QueryColumn, QueryResult
from app.analytics.result_formatter import format_results
from app.core.config import Settings

def _settings() -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_CHART_PAYLOAD_KB=1.0,  # very small for testing truncation
    )

def test_auto_formatting_rules() -> None:
    # revenue -> currency
    # rates -> percent
    # counts -> integer
    # dates -> readable
    # large numbers -> compact
    res = QueryResult(
        columns=[
            QueryColumn("bucket", "DATE"),
            QueryColumn("revenue", "DOUBLE"),
            QueryColumn("discount_percent", "DOUBLE"),
            QueryColumn("user_count", "DOUBLE"),
            QueryColumn("huge_number", "DOUBLE")
        ],
        rows=[
            {
                "bucket": date(2026, 1, 1),
                "revenue": 1500.50,
                "discount_percent": 0.15,
                "user_count": 42.0,
                "huge_number": 2_500_000.0,
            }
        ]
    )
    
    payload = format_results(res, "Title", "Desc", _settings())
    row = payload.data[0]
    
    assert row["formatted_bucket"] == "Jan 01, 2026"
    assert row["formatted_revenue"] == "$1.5k"
    assert row["formatted_discount_percent"] == "15.0%"
    assert row["formatted_user_count"] == "42"
    assert row["formatted_huge_number"] == "2.5M"

def test_truncation_sampling_strategy() -> None:
    # Create an oversized result set
    rows = []
    for i in range(100):
        rows.append({"bucket": date(2026, 1, 1), "revenue": 1000.0 + i})
        
    res = QueryResult(
        columns=[QueryColumn("bucket", "DATE"), QueryColumn("revenue", "DOUBLE")],
        rows=rows
    )
    
    settings = _settings()
    # verify it would be over the cap
    payload = format_results(res, "Title", "Desc", settings)
    
    # Check that it truncated
    assert payload.meta.get("truncated") is True
    assert payload.meta.get("original_row_count") == 100
    
    # Check time series sampling (not naive head cut)
    # The first and last elements should span the full original range roughly
    # Wait, in our dummy data the dates are identical, let's use different dates.
    rows_with_dates = []
    for i in range(100):
        rows_with_dates.append({"bucket": date(2026, 1, 1).replace(day=(i % 28) + 1), "revenue": 1000.0 + i})
        
    res_dates = QueryResult(
        columns=[QueryColumn("bucket", "DATE"), QueryColumn("revenue", "DOUBLE")],
        rows=rows_with_dates
    )
    payload_dates = format_results(res_dates, "Title", "Desc", settings)
    
    assert len(payload_dates.data) < 100
    # ensure last element is the actual last element of the original
    assert payload_dates.data[-1]["revenue"] == 1099.0
    assert payload_dates.data[0]["revenue"] == 1000.0
