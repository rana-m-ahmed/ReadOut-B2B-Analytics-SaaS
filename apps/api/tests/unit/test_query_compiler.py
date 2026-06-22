from __future__ import annotations

from textwrap import dedent

import duckdb

from app.analytics.query_compiler import compile_analytics_intent
from app.core.config import Settings
from app.nlq.intent_validator import (
    DatasetIntentColumn,
    IntentValidationAccepted,
    ValidatedIntent,
    validate_analytics_intent,
)
from app.nlq.schemas import analytics_intent_adapter


def _settings(max_result_rows: int = 500) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_RESULT_ROWS=max_result_rows,
    )


def _columns() -> list[DatasetIntentColumn]:
    return [
        DatasetIntentColumn(name="order_date", data_type="date", unique_count=6),
        DatasetIntentColumn(name="revenue", data_type="number", unique_count=6),
        DatasetIntentColumn(name="region", data_type="category", unique_count=3),
        DatasetIntentColumn(name="units", data_type="number", unique_count=3),
        DatasetIntentColumn(name="discount_percent", data_type="number", unique_count=6),
        DatasetIntentColumn(name="customer_id", data_type="string", unique_count=5),
    ]


def _validated_intent(payload: dict[str, object], *, settings: Settings | None = None) -> ValidatedIntent:
    raw = analytics_intent_adapter.validate_python(payload)
    result = validate_analytics_intent(raw, _columns(), settings or _settings())
    assert isinstance(result, IntentValidationAccepted)
    return result


def _run(compiled_sql: str, params: dict[str, object]) -> list[tuple]:
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            dedent(
                """
                CREATE TABLE dataset(
                    order_date DATE,
                    revenue DOUBLE,
                    region VARCHAR,
                    units INTEGER,
                    discount_percent DOUBLE,
                    customer_id VARCHAR
                )
                """
            )
        )
        connection.execute(
            dedent(
                """
                INSERT INTO dataset VALUES
                    ('2026-01-01', 100, 'West', 2, 0.10, 'c1'),
                    ('2026-01-02', 50, 'East', 1, 0.20, 'c2'),
                    ('2026-01-03', 200, 'West', 3, 0.30, 'c1'),
                    ('2026-01-04', 150, 'East', 2, 0.40, 'c3'),
                    ('2026-01-05', 75, 'North', 1, 0.50, 'c4'),
                    ('2026-01-06', 25, 'West', 1, 0.60, 'c5')
                """
            )
        )
        return connection.execute(compiled_sql, params).fetchall()
    finally:
        connection.close()


def test_single_metric_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "single_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "filters": [{"column": "region", "operator": "eq", "value": "West"}],
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT sum("revenue") AS value
        FROM dataset
        WHERE "region" = $filter_0
        LIMIT $limit
        """
    ).strip()
    assert compiled.params == {"limit": 500, "filter_0": "West"}
    assert _run(compiled.sql, compiled.params) == [(325.0,)]


def test_time_series_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "time_series",
            "metric": "revenue",
            "aggregation": "sum",
            "date_range": {"column": "order_date", "start": "2026-01-01", "end": "2026-01-03"},
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT CAST(date_trunc('day', "order_date") AS DATE) AS bucket,
               sum("revenue") AS value
        FROM dataset
        WHERE "order_date" BETWEEN $date_start AND $date_end
        GROUP BY 1
        ORDER BY 1 ASC
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [
        (duckdb.execute("SELECT DATE '2026-01-01'").fetchone()[0], 100.0),
        (duckdb.execute("SELECT DATE '2026-01-02'").fetchone()[0], 50.0),
        (duckdb.execute("SELECT DATE '2026-01-03'").fetchone()[0], 200.0),
    ]


def test_time_series_preset_uses_dataset_relative_anchor() -> None:
    validated = _validated_intent(
        {
            "intent": "time_series",
            "metric": "revenue",
            "aggregation": "sum",
            "date_range": {"column": "order_date", "preset": "last_30_days"},
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert '(SELECT max("order_date") FROM dataset)' in compiled.sql
    rows = _run(compiled.sql, compiled.params)
    assert len(rows) == 6


def test_grouped_metric_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "grouped_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT "region",
               sum("revenue") AS value
        FROM dataset
        WHERE 1=1
        GROUP BY 1
        ORDER BY value DESC
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [("West", 325.0), ("East", 200.0), ("North", 75.0)]


def test_comparison_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "comparison",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": [],
            "date_range": {"column": "order_date", "start": "2026-01-04", "end": "2026-01-06"},
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        WITH current_period AS (
            SELECT sum("revenue") AS current_value
            FROM dataset
            WHERE 1=1 AND "order_date" BETWEEN $current_start AND $current_end
        ),
        previous_period AS (
            SELECT sum("revenue") AS previous_value
            FROM dataset
            WHERE 1=1 AND "order_date" BETWEEN $previous_start AND $previous_end
        )
        SELECT current_value,
               previous_value,
               current_value - previous_value AS delta_value,
               CASE
                   WHEN previous_value IS NULL OR previous_value = 0 THEN NULL
                   ELSE (current_value - previous_value) * 1.0 / previous_value
               END AS delta_percent
        FROM current_period, previous_period
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [(250.0, 350.0, -100.0, -100.0 / 350.0)]


def test_proportion_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "proportion",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        WITH grouped AS (
            SELECT "region",
                   sum("revenue") AS value
            FROM dataset
            WHERE 1=1
            GROUP BY 1
        )
        SELECT "region",
               value,
               value * 1.0 / SUM(value) OVER () AS proportion
        FROM grouped
        ORDER BY value DESC
        LIMIT $limit
        """
    ).strip()
    rows = _run(compiled.sql, compiled.params)
    assert rows[0][0] == "West"
    assert rows[0][1] == 325.0
    assert round(rows[0][2], 6) == round(325.0 / 600.0, 6)


def test_top_n_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "top_n",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
            "limit": 2,
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT "region",
               sum("revenue") AS value
        FROM dataset
        WHERE 1=1
        GROUP BY 1
        ORDER BY value DESC
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [("West", 325.0), ("East", 200.0)]


def test_bottom_n_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "bottom_n",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
            "limit": 2,
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT "region",
               sum("revenue") AS value
        FROM dataset
        WHERE 1=1
        GROUP BY 1
        ORDER BY value ASC
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [("North", 75.0), ("East", 200.0)]


def test_correlation_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "correlation",
            "metric": "revenue",
            "group_by": ["discount_percent"],
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT 'discount_percent' AS comparison_column,
               corr("revenue", "discount_percent") AS correlation
        FROM dataset
        WHERE 1=1
        LIMIT $limit
        """
    ).strip()
    rows = _run(compiled.sql, compiled.params)
    assert rows[0][0] == "discount_percent"
    assert round(rows[0][1], 6) == round(-0.28697202159177576, 6)


def test_anomaly_explanation_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "anomaly_explanation",
            "metric": "revenue",
            "date_range": {"column": "order_date", "start": "2026-01-04", "end": "2026-01-06"},
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        WITH anomaly_window AS (
            SELECT avg("revenue") AS anomaly_value
            FROM dataset
            WHERE 1=1 AND "order_date" BETWEEN $current_start AND $current_end
        ),
        baseline_window AS (
            SELECT avg("revenue") AS baseline_value
            FROM dataset
            WHERE 1=1 AND "order_date" BETWEEN $previous_start AND $previous_end
        )
        SELECT anomaly_value,
               baseline_value,
               anomaly_value - baseline_value AS delta_value,
               CASE
                   WHEN baseline_value IS NULL OR baseline_value = 0 THEN NULL
                   ELSE (anomaly_value - baseline_value) * 1.0 / baseline_value
               END AS delta_percent
        FROM anomaly_window, baseline_window
        LIMIT $limit
        """
    ).strip()
    rows = _run(compiled.sql, compiled.params)
    assert round(rows[0][0], 6) == round((150.0 + 75.0 + 25.0) / 3.0, 6)
    assert round(rows[0][1], 6) == round((100.0 + 50.0 + 200.0) / 3.0, 6)


def test_clarification_required_compiles_and_executes() -> None:
    validated = _validated_intent(
        {
            "intent": "clarification_required",
            "chart_hint": "table",
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert compiled.sql == dedent(
        """
        SELECT 'clarification_required' AS intent,
               $chart_hint AS chart_hint
        LIMIT $limit
        """
    ).strip()
    assert _run(compiled.sql, compiled.params) == [("clarification_required", "table")]


def test_filter_value_is_parameterized_not_interpolated() -> None:
    malicious_value = "'; DROP TABLE x; --"
    validated = _validated_intent(
        {
            "intent": "single_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "filters": [{"column": "region", "operator": "eq", "value": malicious_value}],
        }
    )

    compiled = compile_analytics_intent(validated, _settings())

    assert malicious_value not in compiled.sql
    assert compiled.params["filter_0"] == malicious_value
