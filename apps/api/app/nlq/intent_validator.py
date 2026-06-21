"""Semantic validation for NLQ intents against the real dataset schema.

This module makes an explicit distinction between reject and clamp:

- Reject means the question cannot be answered safely or faithfully as asked.
  The validator returns a structured rejection with a synthesized
  `clarification_required` intent. Examples: a referenced column does not exist,
  a date range points at a non-date column, or an aggregation needs numeric data
  but the chosen metric is categorical.
- Clamp means the request is still answerable after a safe normalization.
  The validator silently corrects the intent and continues. Examples: a requested
  limit is above `Settings.MAX_RESULT_ROWS`, or a high-cardinality grouping needs
  a forced limit to stay usable.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, get_settings
from app.nlq.schemas import (
    AggregationType,
    AnalyticsIntent,
    ClarificationRequiredIntent,
    DateRange,
    FilterOperator,
)

HIGH_CARDINALITY_THRESHOLD = 200
DEFAULT_HIGH_CARDINALITY_LIMIT = 100
NUMERIC_AGGREGATIONS = {
    AggregationType.SUM,
    AggregationType.AVG,
    AggregationType.MIN,
    AggregationType.MAX,
}
DATE_COLUMN_TYPES = {"date"}
NUMERIC_COLUMN_TYPES = {"number"}
ALLOWED_FILTER_OPERATORS = {
    FilterOperator.EQ,
    FilterOperator.NEQ,
    FilterOperator.GT,
    FilterOperator.LT,
    FilterOperator.BETWEEN,
    FilterOperator.IN,
}
VALID_DATE_PRESETS = {
    "today",
    "yesterday",
    "last_7_days",
    "last_30_days",
    "last_90_days",
    "this_month",
    "last_month",
    "this_year",
    "year_to_date",
}


class DatasetIntentColumn(BaseModel):
    """Real schema facts used for semantic NLQ validation."""

    model_config = ConfigDict(extra="forbid")

    name: str
    data_type: str
    unique_count: int | None = None


class IntentRejectionCode(str, Enum):
    UNKNOWN_COLUMN = "unknown_column"
    NON_NUMERIC_METRIC = "non_numeric_metric"
    INVALID_DATE_COLUMN = "invalid_date_column"
    INVALID_FILTER_OPERATOR = "invalid_filter_operator"
    INVALID_DATE_RANGE = "invalid_date_range"


class IntentRejection(BaseModel):
    """Structured rejection for intents that need clarification."""

    model_config = ConfigDict(extra="forbid")

    code: IntentRejectionCode
    message: str
    clarification_intent: ClarificationRequiredIntent


class ValidatedIntent(BaseModel):
    """Validated intent, optionally normalized by clamps."""

    model_config = ConfigDict(extra="forbid")

    intent: AnalyticsIntent
    clamps: list[str] = Field(default_factory=list)


class IntentValidationAccepted(ValidatedIntent):
    """Accepted semantic validation result."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted"] = "accepted"


class IntentValidationRejected(BaseModel):
    """Rejected intent with a structured reason."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["rejected"] = "rejected"
    rejection: IntentRejection


IntentValidationResult = IntentValidationAccepted | IntentValidationRejected


def validate_analytics_intent(
    intent: AnalyticsIntent,
    dataset_columns: list[DatasetIntentColumn],
    settings: Settings | None = None,
) -> IntentValidationResult:
    """Validate a parsed analytics intent against the real dataset schema."""

    resolved_settings = settings or get_settings()
    columns_by_name = {column.name: column for column in dataset_columns}
    referenced_columns = _referenced_columns(intent)

    for column_name in referenced_columns:
        if column_name not in columns_by_name:
            return _reject(
                IntentRejectionCode.UNKNOWN_COLUMN,
                f"Referenced column '{column_name}' does not exist in the dataset schema",
                intent,
            )

    if intent.metric is not None and intent.aggregation in NUMERIC_AGGREGATIONS:
        metric_column = columns_by_name[intent.metric]
        if metric_column.data_type not in NUMERIC_COLUMN_TYPES:
            return _reject(
                IntentRejectionCode.NON_NUMERIC_METRIC,
                f"Metric column '{intent.metric}' is not numeric for aggregation '{intent.aggregation.value}'",
                intent,
            )

    if intent.date_range is not None:
        date_column = columns_by_name[intent.date_range.column]
        if date_column.data_type not in DATE_COLUMN_TYPES:
            return _reject(
                IntentRejectionCode.INVALID_DATE_COLUMN,
                f"date_range.column '{intent.date_range.column}' is not a date-typed column",
                intent,
            )
        date_range_rejection = _validate_date_range(intent.date_range, intent)
        if date_range_rejection is not None:
            return date_range_rejection

    for filter_clause in intent.filters:
        if filter_clause.operator not in ALLOWED_FILTER_OPERATORS:
            return _reject(
                IntentRejectionCode.INVALID_FILTER_OPERATOR,
                f"Filter operator '{filter_clause.operator.value}' is not supported by the validator allow-list",
                intent,
            )

    clamp_messages: list[str] = []
    normalized_limit = intent.limit

    if normalized_limit is not None and normalized_limit > resolved_settings.MAX_RESULT_ROWS:
        normalized_limit = resolved_settings.MAX_RESULT_ROWS
        clamp_messages.append(
            f"limit clamped to MAX_RESULT_ROWS ({resolved_settings.MAX_RESULT_ROWS})"
        )

    high_cardinality_group = next(
        (
            group_name
            for group_name in intent.group_by
            if (columns_by_name[group_name].unique_count or 0) > HIGH_CARDINALITY_THRESHOLD
        ),
        None,
    )
    if high_cardinality_group is not None and normalized_limit is None:
        normalized_limit = min(DEFAULT_HIGH_CARDINALITY_LIMIT, resolved_settings.MAX_RESULT_ROWS)
        clamp_messages.append(
            f"limit forced to {normalized_limit} because group_by column '{high_cardinality_group}' is high-cardinality"
        )

    if not clamp_messages:
        return IntentValidationAccepted(intent=intent)

    return IntentValidationAccepted(
        intent=intent.model_copy(update={"limit": normalized_limit}),
        clamps=clamp_messages,
    )


def _referenced_columns(intent: AnalyticsIntent) -> set[str]:
    referenced: set[str] = set(intent.group_by)
    if intent.metric is not None:
        referenced.add(intent.metric)
    if intent.date_range is not None:
        referenced.add(intent.date_range.column)
    if intent.sort is not None:
        referenced.add(intent.sort.column)
    for filter_clause in intent.filters:
        referenced.add(filter_clause.column)
    return referenced


def _validate_date_range(
    date_range: DateRange,
    intent: AnalyticsIntent,
) -> IntentValidationRejected | None:
    if date_range.preset is not None:
        if date_range.preset not in VALID_DATE_PRESETS:
            return _reject(
                IntentRejectionCode.INVALID_DATE_RANGE,
                f"date_range preset '{date_range.preset}' is not supported",
                intent,
            )
        return None

    try:
        start = date.fromisoformat(date_range.start or "")
        end = date.fromisoformat(date_range.end or "")
    except ValueError:
        return _reject(
            IntentRejectionCode.INVALID_DATE_RANGE,
            "date_range start/end must be valid ISO dates",
            intent,
        )

    if start > end:
        return _reject(
            IntentRejectionCode.INVALID_DATE_RANGE,
            "date_range start must be on or before end",
            intent,
        )
    return None


def _reject(code: IntentRejectionCode, message: str, intent: AnalyticsIntent) -> IntentValidationRejected:
    return IntentValidationRejected(
        rejection=IntentRejection(
            code=code,
            message=message,
            clarification_intent=ClarificationRequiredIntent(
                intent="clarification_required",
                chart_hint=intent.chart_hint,
            ),
        )
    )
