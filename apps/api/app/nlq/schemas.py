"""Strict NLQ intent schemas for the analytics planning contract."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


class IntentType(str, Enum):
    SINGLE_METRIC = "single_metric"
    TIME_SERIES = "time_series"
    GROUPED_METRIC = "grouped_metric"
    COMPARISON = "comparison"
    PROPORTION = "proportion"
    TOP_N = "top_n"
    BOTTOM_N = "bottom_n"
    CORRELATION = "correlation"
    ANOMALY_EXPLANATION = "anomaly_explanation"
    CLARIFICATION_REQUIRED = "clarification_required"


class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"


class FilterOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class StrictSchemaModel(BaseModel):
    """Shared strict validation settings for LLM-emitted contract payloads."""

    model_config = ConfigDict(extra="forbid")


class DateRange(StrictSchemaModel):
    """Date range constraint using internal safe column names only."""

    column: str
    preset: str | None = None
    start: str | None = None
    end: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> DateRange:
        has_preset = self.preset is not None
        has_explicit_bounds = self.start is not None or self.end is not None
        if has_preset == has_explicit_bounds:
            raise ValueError("date_range must provide either preset or start/end")
        if has_explicit_bounds and (self.start is None or self.end is None):
            raise ValueError("date_range start and end must both be provided")
        return self


class IntentFilter(StrictSchemaModel):
    """Structured filter clause using internal safe column names only."""

    column: str
    operator: FilterOperator
    value: Any


class SortClause(StrictSchemaModel):
    """Sort definition using internal safe column names only."""

    column: str
    direction: SortDirection = SortDirection.DESC


class BaseAnalyticsIntent(StrictSchemaModel):
    """Common fields shared by all analytics intents."""

    metric: str | None = None
    aggregation: AggregationType | None = None
    group_by: list[str] = Field(default_factory=list)
    date_range: DateRange | None = None
    filters: list[IntentFilter] = Field(default_factory=list)
    sort: SortClause | None = None
    limit: int | None = Field(default=None, ge=1)
    chart_hint: str | None = None


class SingleMetricIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.SINGLE_METRIC]
    metric: str
    aggregation: AggregationType


class TimeSeriesIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.TIME_SERIES]
    metric: str
    aggregation: AggregationType


class GroupedMetricIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.GROUPED_METRIC]
    metric: str
    aggregation: AggregationType
    group_by: list[str] = Field(min_length=1)


class ComparisonIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.COMPARISON]
    metric: str
    aggregation: AggregationType
    group_by: list[str] = Field(default_factory=list)


class ProportionIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.PROPORTION]
    metric: str
    aggregation: AggregationType
    group_by: list[str] = Field(min_length=1)


class TopNIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.TOP_N]
    metric: str
    aggregation: AggregationType
    group_by: list[str] = Field(min_length=1)
    limit: int = Field(ge=1)


class BottomNIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.BOTTOM_N]
    metric: str
    aggregation: AggregationType
    group_by: list[str] = Field(min_length=1)
    limit: int = Field(ge=1)


class CorrelationIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.CORRELATION]
    metric: str
    group_by: list[str] = Field(min_length=1)


class AnomalyExplanationIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.ANOMALY_EXPLANATION]
    metric: str


class ClarificationRequiredIntent(BaseAnalyticsIntent):
    intent: Literal[IntentType.CLARIFICATION_REQUIRED]


AnalyticsIntent = Annotated[
    SingleMetricIntent
    | TimeSeriesIntent
    | GroupedMetricIntent
    | ComparisonIntent
    | ProportionIntent
    | TopNIntent
    | BottomNIntent
    | CorrelationIntent
    | AnomalyExplanationIntent
    | ClarificationRequiredIntent,
    Field(discriminator="intent"),
]

analytics_intent_adapter = TypeAdapter(AnalyticsIntent)
