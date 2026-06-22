"""Deterministic query resolution helpers for follow-ups and common fresh asks."""

from __future__ import annotations

import re
from calendar import month_name
from typing import Literal

from app.db.models import DatasetColumn
from app.nlq.schemas import (
    AggregationType,
    AnalyticsIntent,
    AnomalyExplanationIntent,
    ComparisonIntent,
    DateRange,
    FilterOperator,
    GroupedMetricIntent,
    IntentFilter,
    IntentType,
    ProportionIntent,
    SingleMetricIntent,
    TimeSeriesIntent,
    TopNIntent,
    BottomNIntent,
    CorrelationIntent,
)


def _get_valid_charts(intent: IntentType) -> set[str]:
    return {
        IntentType.SINGLE_METRIC: {"metric_card"},
        IntentType.TIME_SERIES: {"line", "bar", "multi_line"},
        IntentType.GROUPED_METRIC: {"bar", "donut", "table"},
        IntentType.PROPORTION: {"donut", "table"},
        IntentType.TOP_N: {"bar", "table"},
        IntentType.BOTTOM_N: {"bar", "table"},
        IntentType.CORRELATION: {"scatter", "table"},
        IntentType.COMPARISON: {"metric_card", "line", "bar", "table"},
        IntentType.ANOMALY_EXPLANATION: {"line_with_highlighted_point", "line", "table"},
    }.get(intent, {"table"})


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _normalize_identifier(value: str) -> str:
    return _normalize_text(value).replace(" ", "_")


def _column_aliases(column: DatasetColumn) -> set[str]:
    aliases = {_normalize_identifier(column.name), _normalize_text(column.name)}
    if column.display_name:
        aliases.add(_normalize_identifier(column.display_name))
        aliases.add(_normalize_text(column.display_name))
    return {alias for alias in aliases if alias}


def _match_column(term: str, dataset_columns: list[DatasetColumn]) -> DatasetColumn | None:
    normalized_term = _normalize_text(term)
    normalized_identifier = normalized_term.replace(" ", "_")
    for column in dataset_columns:
        aliases = _column_aliases(column)
        if normalized_term in aliases or normalized_identifier in aliases:
            return column
        if any(
            normalized_term in alias
            or alias in normalized_term
            or normalized_identifier in alias
            or alias in normalized_identifier
            for alias in aliases
        ):
            return column
    return None


def _find_column_by_keyword(dataset_columns: list[DatasetColumn], *keywords: str) -> DatasetColumn | None:
    keyword_set = {_normalize_text(keyword) for keyword in keywords}
    for column in dataset_columns:
        aliases = _column_aliases(column)
        if aliases & keyword_set:
            return column
    for column in dataset_columns:
        haystack = " ".join(sorted(_column_aliases(column)))
        if any(keyword in haystack for keyword in keyword_set):
            return column
    return None


def _find_primary_date_column(dataset_columns: list[DatasetColumn]) -> DatasetColumn | None:
    for column in dataset_columns:
        if column.data_type == "date":
            return column
    return None


def _find_revenue_metric(dataset_columns: list[DatasetColumn]) -> DatasetColumn | None:
    return _find_column_by_keyword(dataset_columns, "revenue", "sales", "gross_margin")


def _find_order_metric(dataset_columns: list[DatasetColumn]) -> DatasetColumn | None:
    order_id = _find_column_by_keyword(dataset_columns, "order_id", "order id")
    if order_id is not None:
        return order_id
    for column in dataset_columns:
        if column.semantic_role == "identifier":
            return column
    return None


def _find_dimension_for_phrase(question_lower: str, dataset_columns: list[DatasetColumn]) -> DatasetColumn | None:
    candidate_phrases = [
        "product category",
        "product categories",
        "category",
        "categories",
        "region",
        "channel",
        "channels",
        "marketing channel",
        "customer type",
        "payment method",
    ]
    for phrase in candidate_phrases:
        if phrase in question_lower:
            matched = _match_column(phrase, dataset_columns)
            if matched is None and phrase in {"category", "categories"}:
                matched = _find_column_by_keyword(dataset_columns, "product_category", "product category", "category")
            if matched is None and phrase in {"channel", "channels"}:
                matched = _find_column_by_keyword(dataset_columns, "marketing_channel", "marketing channel", "channel")
            if matched is not None:
                return matched
    return None


def _filter_for_literal_value(
    question_lower: str,
    dataset_columns: list[DatasetColumn],
) -> list[IntentFilter]:
    filters: list[IntentFilter] = []
    for column in dataset_columns:
        for sample in column.sample_values or []:
            if sample is None:
                continue
            normalized_sample = _normalize_text(str(sample))
            if normalized_sample and normalized_sample in question_lower:
                filters.append(IntentFilter(column=column.name, operator=FilterOperator.EQ, value=sample))
                break
    return filters


def _date_range_from_question(question_lower: str, dataset_columns: list[DatasetColumn]) -> DateRange | None:
    date_column = _find_primary_date_column(dataset_columns)
    if date_column is None:
        return None

    preset_by_phrase = {
        "last quarter": "last_quarter",
        "this quarter": "this_quarter",
        "last month": "last_month",
        "this month": "this_month",
        "this year": "this_year",
        "year to date": "year_to_date",
        "last 90 days": "last_90_days",
        "last 30 days": "last_30_days",
        "last 7 days": "last_7_days",
    }
    for phrase, preset in preset_by_phrase.items():
        if phrase in question_lower:
            return DateRange(column=date_column.name, preset=preset)

    month_mentions = [name.lower() for name in month_name if name and name.lower() in question_lower]
    if month_mentions:
        # Month-only questions are still useful enough to anchor to the dataset year.
        # The compiler interprets `this_year` relative to the dataset's max date.
        return DateRange(column=date_column.name, preset="this_year")

    return None


def _default_comparison_date_range(dataset_columns: list[DatasetColumn]) -> DateRange | None:
    date_column = _find_primary_date_column(dataset_columns)
    if date_column is None:
        return None
    return DateRange(column=date_column.name, preset="last_30_days")


def _chart_hint_from_question(question_lower: str) -> str | None:
    chart_aliases = {
        "line chart": "line",
        "bar chart": "bar",
        "pie chart": "donut",
        "donut chart": "donut",
        "table": "table",
    }
    for phrase, chart_type in chart_aliases.items():
        if phrase in question_lower:
            return chart_type
    return None


def resolve_fresh_question(
    question: str,
    dataset_columns: list[DatasetColumn],
) -> AnalyticsIntent | Literal["defer_to_llm"]:
    """Resolve common fresh asks without spending an LLM call."""

    question_lower = _normalize_text(question)
    revenue_metric = _find_revenue_metric(dataset_columns)
    order_metric = _find_order_metric(dataset_columns)
    dimension = _find_dimension_for_phrase(question_lower, dataset_columns)
    date_range = _date_range_from_question(question_lower, dataset_columns)
    explicit_filters = _filter_for_literal_value(question_lower, dataset_columns)

    if "revenue and orders together" in question_lower:
        return "defer_to_llm"

    if "summarize the dataset" in question_lower:
        summary_metric = revenue_metric or order_metric
        summary_dimension = dimension or _find_column_by_keyword(
            dataset_columns,
            "region",
            "product_category",
            "product category",
            "marketing_channel",
            "marketing channel",
        )
        if summary_metric is not None and summary_dimension is not None:
            aggregation = AggregationType.COUNT if summary_metric is order_metric else AggregationType.SUM
            return GroupedMetricIntent(
                intent=IntentType.GROUPED_METRIC,
                metric=summary_metric.name,
                aggregation=aggregation,
                group_by=[summary_dimension.name],
                chart_hint="bar",
            )
        if summary_metric is not None:
            aggregation = AggregationType.COUNT if summary_metric is order_metric else AggregationType.SUM
            return SingleMetricIntent(
                intent=IntentType.SINGLE_METRIC,
                metric=summary_metric.name,
                aggregation=aggregation,
            )
        return "defer_to_llm"

    if ("dip" in question_lower or "unusual drop" in question_lower or "unusual drops" in question_lower) and revenue_metric is not None:
        return AnomalyExplanationIntent(
            intent=IntentType.ANOMALY_EXPLANATION,
            metric=revenue_metric.name,
            aggregation=AggregationType.AVG,
            date_range=date_range or _default_comparison_date_range(dataset_columns),
            chart_hint="line",
        )

    if "changed last month" in question_lower and revenue_metric is not None:
        return ComparisonIntent(
            intent=IntentType.COMPARISON,
            metric=revenue_metric.name,
            aggregation=AggregationType.SUM,
            date_range=DateRange(
                column=_find_primary_date_column(dataset_columns).name,
                preset="last_month",
            ),
            chart_hint="bar",
        )

    if ("compare" in question_lower and "previous period" in question_lower and revenue_metric is not None):
        return ComparisonIntent(
            intent=IntentType.COMPARISON,
            metric=revenue_metric.name,
            aggregation=AggregationType.SUM,
            group_by=[dimension.name] if dimension is not None else [],
            date_range=date_range or _default_comparison_date_range(dataset_columns),
        )

    if ("grew fastest" in question_lower or "growth" in question_lower) and revenue_metric is not None:
        growth_dimension = dimension or _find_column_by_keyword(dataset_columns, "product_category", "product category", "category")
        if growth_dimension is not None:
            return ComparisonIntent(
                intent=IntentType.COMPARISON,
                metric=revenue_metric.name,
                aggregation=AggregationType.SUM,
                group_by=[growth_dimension.name],
                date_range=date_range or _default_comparison_date_range(dataset_columns),
                chart_hint="bar",
            )

    limit_match = re.search(r"\b(top|bottom)\s+(\d+)", question_lower)
    requested_limit = int(limit_match.group(2)) if limit_match else None

    if ("top" in question_lower or "best" in question_lower or "highest" in question_lower) and revenue_metric is not None:
        if "month" in question_lower and _find_primary_date_column(dataset_columns) is not None:
            return TimeSeriesIntent(
                intent=IntentType.TIME_SERIES,
                metric=revenue_metric.name,
                aggregation=AggregationType.SUM,
                date_range=date_range or DateRange(
                    column=_find_primary_date_column(dataset_columns).name,
                    preset="this_year",
                ),
                chart_hint="line",
            )

        ranked_dimension = dimension
        if ranked_dimension is not None:
            return TopNIntent(
                intent=IntentType.TOP_N,
                metric=revenue_metric.name,
                aggregation=AggregationType.AVG if ("aov" in question_lower or "average order value" in question_lower) else AggregationType.SUM,
                group_by=[ranked_dimension.name],
                limit=requested_limit or 1,
                date_range=date_range,
                filters=explicit_filters,
                chart_hint="bar",
            )

    if ("worst" in question_lower or "bottom" in question_lower) and dimension is not None:
        metric = order_metric if "order" in question_lower and order_metric is not None else revenue_metric
        aggregation = AggregationType.COUNT if metric is order_metric else AggregationType.SUM
        if metric is not None:
            return BottomNIntent(
                intent=IntentType.BOTTOM_N,
                metric=metric.name,
                aggregation=aggregation,
                group_by=[dimension.name],
                limit=requested_limit or 1,
                date_range=date_range,
                filters=explicit_filters,
                chart_hint="bar",
            )

    if ("share" in question_lower or "percentage" in question_lower) and revenue_metric is not None and dimension is not None:
        return ProportionIntent(
            intent=IntentType.PROPORTION,
            metric=revenue_metric.name,
            aggregation=AggregationType.SUM,
            group_by=[dimension.name],
            date_range=date_range,
            filters=explicit_filters,
            chart_hint="donut",
        )

    if ("average order value" in question_lower or "aov" in question_lower) and revenue_metric is not None and dimension is not None:
        return GroupedMetricIntent(
            intent=IntentType.GROUPED_METRIC,
            metric=revenue_metric.name,
            aggregation=AggregationType.AVG,
            group_by=[dimension.name],
            date_range=date_range,
            filters=explicit_filters,
            chart_hint="bar",
        )

    if ("discount impact" in question_lower or "correlation" in question_lower) and revenue_metric is not None:
        correlation_dimension = _find_column_by_keyword(dataset_columns, "discount_percent", "discount percent")
        if correlation_dimension is not None:
            return CorrelationIntent(
                intent=IntentType.CORRELATION,
                metric=revenue_metric.name,
                group_by=[correlation_dimension.name],
                date_range=date_range,
                filters=explicit_filters,
                chart_hint="scatter",
            )

    if ("over time" in question_lower or "trend" in question_lower) and revenue_metric is not None:
        date_column = _find_primary_date_column(dataset_columns)
        if date_column is not None:
            return TimeSeriesIntent(
                intent=IntentType.TIME_SERIES,
                metric=revenue_metric.name,
                aggregation=AggregationType.SUM,
                date_range=date_range or DateRange(column=date_column.name, preset="this_year"),
                filters=explicit_filters,
                chart_hint="line",
            )

    if "orders by" in question_lower and order_metric is not None and dimension is not None:
        return GroupedMetricIntent(
            intent=IntentType.GROUPED_METRIC,
            metric=order_metric.name,
            aggregation=AggregationType.COUNT,
            group_by=[dimension.name],
            date_range=date_range,
            filters=explicit_filters,
            chart_hint="bar",
        )

    if "compare" in question_lower:
        compared_dimension = dimension
        if compared_dimension is None:
            compared_dimension = _find_column_by_keyword(dataset_columns, "customer_type", "customer type")
        if compared_dimension is not None and revenue_metric is not None:
            filters = explicit_filters
            return GroupedMetricIntent(
                intent=IntentType.GROUPED_METRIC,
                metric=revenue_metric.name,
                aggregation=AggregationType.SUM,
                group_by=[compared_dimension.name],
                date_range=date_range,
                filters=filters,
                chart_hint="bar",
            )

    if "by" in question_lower and dimension is not None:
        metric = revenue_metric
        aggregation = AggregationType.SUM
        if ("orders" in question_lower or "order" in question_lower) and order_metric is not None:
            metric = order_metric
            aggregation = AggregationType.COUNT
        if metric is not None:
            intent_cls = GroupedMetricIntent
            if requested_limit and "top" in question_lower:
                intent_cls = TopNIntent
            elif requested_limit and "bottom" in question_lower:
                intent_cls = BottomNIntent

            if intent_cls is TopNIntent:
                return TopNIntent(
                    intent=IntentType.TOP_N,
                    metric=metric.name,
                    aggregation=aggregation,
                    group_by=[dimension.name],
                    limit=requested_limit,
                    date_range=date_range,
                    filters=explicit_filters,
                    chart_hint="bar",
                )
            if intent_cls is BottomNIntent:
                return BottomNIntent(
                    intent=IntentType.BOTTOM_N,
                    metric=metric.name,
                    aggregation=aggregation,
                    group_by=[dimension.name],
                    limit=requested_limit,
                    date_range=date_range,
                    filters=explicit_filters,
                    chart_hint="bar",
                )
            return GroupedMetricIntent(
                intent=IntentType.GROUPED_METRIC,
                metric=metric.name,
                aggregation=aggregation,
                group_by=[dimension.name],
                date_range=date_range,
                filters=explicit_filters,
                chart_hint="bar",
            )

    if "for the " in question_lower and revenue_metric is not None:
        if explicit_filters:
            return SingleMetricIntent(
                intent=IntentType.SINGLE_METRIC,
                metric=revenue_metric.name,
                aggregation=AggregationType.SUM,
                filters=explicit_filters,
            )

    return "defer_to_llm"


def resolve_context(
    prior_intent: AnalyticsIntent,
    new_question: str,
    dataset_columns: list[DatasetColumn]
) -> AnalyticsIntent | Literal["treat_as_fresh"]:
    """
    Deterministically merge a follow-up question into a prior intent using fixed patterns.
    If it doesn't match a known pattern, return 'treat_as_fresh' to route it to the LLM.
    """
    question_lower = _normalize_text(new_question)

    # Pattern 1: "break that down by X" or "break down by X"
    match_breakdown = re.search(r"(?:break that down by|break down by)\s+(.+)", question_lower)
    if match_breakdown:
        col_name = match_breakdown.group(1).strip()
        matched_col = _match_column(col_name, dataset_columns)
        if matched_col:
            from app.nlq.schemas import analytics_intent_adapter
            intent_dict = prior_intent.model_dump(exclude_none=True)
            intent_dict["group_by"] = [matched_col.name]
            if intent_dict["intent"] in (IntentType.SINGLE_METRIC.value, IntentType.TIME_SERIES.value):
                intent_dict["intent"] = IntentType.GROUPED_METRIC.value
            return analytics_intent_adapter.validate_python(intent_dict)

    # Pattern 2: "compare with previous period"
    if "compare with previous period" in question_lower or ("compare" in question_lower and "previous" in question_lower):
        from app.nlq.schemas import analytics_intent_adapter
        intent_dict = prior_intent.model_dump(exclude_none=True)
        intent_dict["intent"] = IntentType.COMPARISON.value
        if intent_dict.get("date_range") is None:
            inferred_date_range = _default_comparison_date_range(dataset_columns)
            if inferred_date_range is not None:
                intent_dict["date_range"] = inferred_date_range.model_dump(exclude_none=True)
        return analytics_intent_adapter.validate_python(intent_dict)

    # Pattern 3: "only for returning customers" -> filter
    match_filter = re.search(r"only for\s+(.+)", question_lower)
    if match_filter:
        val_str = match_filter.group(1).strip()
        for col in dataset_columns:
            if not col.sample_values:
                continue
            for sample in col.sample_values:
                if sample is not None and _normalize_text(str(sample)) in val_str:
                    new_intent = prior_intent.model_copy(deep=True)
                    new_intent.filters.append(IntentFilter(
                        column=col.name,
                        operator=FilterOperator.EQ,
                        value=sample
                    ))
                    return new_intent

    # Pattern 4: "show as a X chart"
    chart_type = _chart_hint_from_question(question_lower)
    if chart_type is not None:
        valid_charts = _get_valid_charts(prior_intent.intent)
        if chart_type in valid_charts:
            new_intent = prior_intent.model_copy(deep=True)
            new_intent.chart_hint = chart_type
            return new_intent

    # Pattern 5: "what caused that?" -> ranked-breakdown candidate
    if "what caused that" in question_lower or "why did" in question_lower:
        candidates = [c for c in dataset_columns if c.semantic_role == "dimension" or c.data_type == "category"]
        if candidates:
            best_col = candidates[0]
            from app.nlq.schemas import analytics_intent_adapter
            intent_dict = prior_intent.model_dump(exclude_none=True)
            intent_dict["intent"] = IntentType.GROUPED_METRIC.value
            intent_dict["group_by"] = [best_col.name]
            return analytics_intent_adapter.validate_python(intent_dict)

    return "treat_as_fresh"
