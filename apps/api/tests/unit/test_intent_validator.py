from __future__ import annotations

from app.core.config import Settings
from app.nlq.intent_validator import (
    DatasetIntentColumn,
    IntentValidationAccepted,
    IntentValidationRejected,
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
        DatasetIntentColumn(name="revenue", data_type="number", unique_count=90),
        DatasetIntentColumn(name="order_date", data_type="date", unique_count=365),
        DatasetIntentColumn(name="region", data_type="category", unique_count=5),
        DatasetIntentColumn(name="customer_id", data_type="string", unique_count=5000),
        DatasetIntentColumn(name="notes", data_type="string", unique_count=50),
    ]


def test_nonexistent_column_returns_rejection() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "single_metric",
            "metric": "profit",
            "aggregation": "sum",
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings())

    assert isinstance(result, IntentValidationRejected)
    assert result.rejection.code == "unknown_column"
    assert result.rejection.clarification_intent.intent == "clarification_required"


def test_non_numeric_metric_with_sum_returns_rejection() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "single_metric",
            "metric": "notes",
            "aggregation": "sum",
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings())

    assert isinstance(result, IntentValidationRejected)
    assert result.rejection.code == "non_numeric_metric"


def test_valid_intent_passes_unchanged() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "grouped_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
            "limit": 20,
            "date_range": {"column": "order_date", "preset": "last_30_days"},
            "filters": [{"column": "region", "operator": "eq", "value": "West"}],
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings())

    assert isinstance(result, IntentValidationAccepted)
    assert result.intent == intent
    assert result.clamps == []


def test_limit_above_max_result_rows_gets_clamped() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "top_n",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["region"],
            "limit": 10000,
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings(max_result_rows=250))

    assert isinstance(result, IntentValidationAccepted)
    assert result.intent.limit == 250
    assert any("MAX_RESULT_ROWS" in clamp for clamp in result.clamps)


def test_unsupported_filter_operator_returns_rejection() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "single_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "filters": [{"column": "region", "operator": "gte", "value": "West"}],
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings())

    assert isinstance(result, IntentValidationRejected)
    assert result.rejection.code == "invalid_filter_operator"


def test_high_cardinality_group_by_without_limit_gets_force_limited() -> None:
    intent = analytics_intent_adapter.validate_python(
        {
            "intent": "grouped_metric",
            "metric": "revenue",
            "aggregation": "sum",
            "group_by": ["customer_id"],
        }
    )

    result = validate_analytics_intent(intent, _columns(), _settings(max_result_rows=80))

    assert isinstance(result, IntentValidationAccepted)
    assert result.intent.limit == 80
    assert any("high-cardinality" in clamp for clamp in result.clamps)
