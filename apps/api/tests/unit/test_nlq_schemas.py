from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.nlq.schemas import IntentType, analytics_intent_adapter


@pytest.mark.parametrize(
    ("payload", "expected_intent"),
    [
        (
            {
                "intent": "single_metric",
                "metric": "revenue",
                "aggregation": "sum",
                "filters": [{"column": "region", "operator": "eq", "value": "West"}],
            },
            IntentType.SINGLE_METRIC,
        ),
        (
            {
                "intent": "time_series",
                "metric": "revenue",
                "aggregation": "sum",
                "date_range": {"column": "order_date", "preset": "last_30_days"},
                "chart_hint": "line",
            },
            IntentType.TIME_SERIES,
        ),
        (
            {
                "intent": "grouped_metric",
                "metric": "revenue",
                "aggregation": "avg",
                "group_by": ["region"],
            },
            IntentType.GROUPED_METRIC,
        ),
        (
            {
                "intent": "comparison",
                "metric": "revenue",
                "aggregation": "sum",
                "group_by": ["customer_type"],
                "sort": {"column": "revenue", "direction": "desc"},
            },
            IntentType.COMPARISON,
        ),
        (
            {
                "intent": "proportion",
                "metric": "units",
                "aggregation": "sum",
                "group_by": ["product_category"],
                "chart_hint": "pie",
            },
            IntentType.PROPORTION,
        ),
        (
            {
                "intent": "top_n",
                "metric": "revenue",
                "aggregation": "sum",
                "group_by": ["region"],
                "limit": 5,
            },
            IntentType.TOP_N,
        ),
        (
            {
                "intent": "bottom_n",
                "metric": "gross_margin",
                "aggregation": "avg",
                "group_by": ["marketing_channel"],
                "limit": 3,
            },
            IntentType.BOTTOM_N,
        ),
        (
            {
                "intent": "correlation",
                "metric": "revenue",
                "group_by": ["discount_percent"],
            },
            IntentType.CORRELATION,
        ),
        (
            {
                "intent": "anomaly_explanation",
                "metric": "revenue",
                "date_range": {
                    "column": "order_date",
                    "start": "2026-04-01",
                    "end": "2026-04-07",
                },
            },
            IntentType.ANOMALY_EXPLANATION,
        ),
        (
            {
                "intent": "clarification_required",
                "chart_hint": "table",
            },
            IntentType.CLARIFICATION_REQUIRED,
        ),
    ],
)
def test_analytics_intent_parses_each_supported_intent_type(
    payload: dict[str, object],
    expected_intent: IntentType,
) -> None:
    parsed = analytics_intent_adapter.validate_python(payload)

    assert parsed.intent == expected_intent


def test_analytics_intent_rejects_unknown_aggregation_value() -> None:
    with pytest.raises(ValidationError, match="aggregation"):
        analytics_intent_adapter.validate_python(
            {
                "intent": "single_metric",
                "metric": "revenue",
                "aggregation": "median",
            }
        )


def test_analytics_intent_rejects_unexpected_extra_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        analytics_intent_adapter.validate_python(
            {
                "intent": "single_metric",
                "metric": "revenue",
                "aggregation": "sum",
                "hallucinated_field": "should not exist",
            }
        )
