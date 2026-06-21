"""Compile validated analytics intents into parameterized DuckDB SQL."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.core.config import Settings, get_settings
from app.core.errors import QueryCompilationError
from app.nlq.intent_validator import ValidatedIntent
from app.nlq.schemas import AggregationType, DateRange, FilterOperator, IntentType, SortDirection

DATASET_TABLE_NAME = "dataset"


@dataclass(slots=True, frozen=True)
class CompiledQuery:
    """Parameterized SQL ready for DuckDB execution."""

    sql: str
    params: dict[str, Any]


def compile_analytics_intent(
    validated_intent: ValidatedIntent,
    settings: Settings | None = None,
) -> CompiledQuery:
    """Compile a validated intent into parameterized SQL and named parameters."""

    resolved_settings = settings or get_settings()
    intent = validated_intent.intent
    limit = intent.limit or resolved_settings.MAX_RESULT_ROWS

    match intent.intent:
        case IntentType.SINGLE_METRIC:
            return _compile_single_metric(intent.metric, intent.aggregation, intent, limit)
        case IntentType.TIME_SERIES:
            return _compile_time_series(intent.metric, intent.aggregation, intent, limit)
        case IntentType.GROUPED_METRIC:
            return _compile_grouped_metric(intent.metric, intent.aggregation, intent, limit)
        case IntentType.COMPARISON:
            return _compile_comparison(intent.metric, intent.aggregation, intent, limit)
        case IntentType.PROPORTION:
            return _compile_proportion(intent.metric, intent.aggregation, intent, limit)
        case IntentType.TOP_N:
            return _compile_ranked_metric(intent.metric, intent.aggregation, intent, limit, descending=True)
        case IntentType.BOTTOM_N:
            return _compile_ranked_metric(intent.metric, intent.aggregation, intent, limit, descending=False)
        case IntentType.CORRELATION:
            return _compile_correlation(intent.metric, intent.group_by[0], intent, limit)
        case IntentType.ANOMALY_EXPLANATION:
            return _compile_anomaly_explanation(intent.metric, intent, limit)
        case IntentType.CLARIFICATION_REQUIRED:
            return _compile_clarification_required(intent.chart_hint, limit)
        case _:
            raise QueryCompilationError(f"Unsupported intent type '{intent.intent}'")


def _compile_single_metric(metric: str, aggregation: AggregationType, intent: Any, limit: int) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    where_clause = _build_where_clause(intent, params)
    sql = (
        f'SELECT {aggregation.value}("{metric}") AS value\n'
        f'FROM {DATASET_TABLE_NAME}\n'
        f"{where_clause}\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_time_series(metric: str, aggregation: AggregationType, intent: Any, limit: int) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    granularity = _resolve_time_granularity(intent.date_range)
    where_clause = _build_where_clause(intent, params)
    sql = (
        f'SELECT CAST(date_trunc(\'{granularity}\', "{intent.date_range.column}") AS DATE) AS bucket,\n'
        f'       {aggregation.value}("{metric}") AS value\n'
        f'FROM {DATASET_TABLE_NAME}\n'
        f"{where_clause}\n"
        "GROUP BY 1\n"
        "ORDER BY 1 ASC\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_grouped_metric(metric: str, aggregation: AggregationType, intent: Any, limit: int) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    where_clause = _build_where_clause(intent, params)
    group_select = _group_select(intent.group_by)
    order_clause = _resolve_order_clause(intent, default_column="value", default_direction="DESC")
    sql = (
        f"SELECT {group_select},\n"
        f'       {aggregation.value}("{metric}") AS value\n'
        f'FROM {DATASET_TABLE_NAME}\n'
        f"{where_clause}\n"
        f"GROUP BY {', '.join(str(index) for index in range(1, len(intent.group_by) + 1))}\n"
        f"{order_clause}\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_ranked_metric(
    metric: str,
    aggregation: AggregationType,
    intent: Any,
    limit: int,
    *,
    descending: bool,
) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    where_clause = _build_where_clause(intent, params)
    group_select = _group_select(intent.group_by)
    direction = "DESC" if descending else "ASC"
    sql = (
        f"SELECT {group_select},\n"
        f'       {aggregation.value}("{metric}") AS value\n'
        f'FROM {DATASET_TABLE_NAME}\n'
        f"{where_clause}\n"
        f"GROUP BY {', '.join(str(index) for index in range(1, len(intent.group_by) + 1))}\n"
        f"ORDER BY value {direction}\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_proportion(metric: str, aggregation: AggregationType, intent: Any, limit: int) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    where_clause = _build_where_clause(intent, params)
    group_select = _group_select(intent.group_by)
    grouped_by = ", ".join(str(index) for index in range(1, len(intent.group_by) + 1))
    order_clause = _resolve_order_clause(intent, default_column="value", default_direction="DESC")
    sql = (
        "WITH grouped AS (\n"
        f"    SELECT {group_select},\n"
        f'           {aggregation.value}("{metric}") AS value\n'
        f"    FROM {DATASET_TABLE_NAME}\n"
        f"    {where_clause}\n"
        f"    GROUP BY {grouped_by}\n"
        ")\n"
        f"SELECT {group_select},\n"
        "       value,\n"
        "       value * 1.0 / SUM(value) OVER () AS proportion\n"
        "FROM grouped\n"
        f"{order_clause}\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_correlation(metric: str, dimension: str, intent: Any, limit: int) -> CompiledQuery:
    params: dict[str, Any] = {"limit": limit}
    where_clause = _build_where_clause(intent, params)
    sql = (
        f"SELECT '{dimension}' AS comparison_column,\n"
        f'       corr("{metric}", "{dimension}") AS correlation\n'
        f'FROM {DATASET_TABLE_NAME}\n'
        f"{where_clause}\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_comparison(metric: str, aggregation: AggregationType, intent: Any, limit: int) -> CompiledQuery:
    if intent.date_range is None:
        raise QueryCompilationError("comparison intent requires a validated date_range")

    params: dict[str, Any] = {"limit": limit}
    period = _resolve_comparison_period(intent.date_range)
    params.update(period)
    non_date_where = _build_where_clause(intent, params, include_date_range=False)

    if intent.group_by:
        group_select = _group_select(intent.group_by)
        group_by_ordinals = ", ".join(str(index) for index in range(1, len(intent.group_by) + 1))
        join_using = ", ".join(f'"{column}"' for column in intent.group_by)
        coalesced_columns = ", ".join(
            f'COALESCE(current_period."{column}", previous_period."{column}") AS "{column}"'
            for column in intent.group_by
        )
        sql = (
            "WITH current_period AS (\n"
            f"    SELECT {group_select},\n"
            f'           {aggregation.value}("{metric}") AS current_value\n'
            f"    FROM {DATASET_TABLE_NAME}\n"
            f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $current_start AND $current_end\n"
            f"    GROUP BY {group_by_ordinals}\n"
            "),\n"
            "previous_period AS (\n"
            f"    SELECT {group_select},\n"
            f'           {aggregation.value}("{metric}") AS previous_value\n'
            f"    FROM {DATASET_TABLE_NAME}\n"
            f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $previous_start AND $previous_end\n"
            f"    GROUP BY {group_by_ordinals}\n"
            ")\n"
            f"SELECT {coalesced_columns},\n"
            "       current_period.current_value,\n"
            "       previous_period.previous_value,\n"
            "       current_period.current_value - previous_period.previous_value AS delta_value,\n"
            "       CASE\n"
            "           WHEN previous_period.previous_value IS NULL OR previous_period.previous_value = 0 THEN NULL\n"
            "           ELSE (current_period.current_value - previous_period.previous_value) * 1.0 / previous_period.previous_value\n"
            "       END AS delta_percent\n"
            "FROM current_period\n"
            f"FULL OUTER JOIN previous_period USING ({join_using})\n"
            "ORDER BY delta_value DESC\n"
            "LIMIT $limit"
        )
        return CompiledQuery(sql=sql, params=params)

    sql = (
        "WITH current_period AS (\n"
        f'    SELECT {aggregation.value}("{metric}") AS current_value\n'
        f"    FROM {DATASET_TABLE_NAME}\n"
        f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $current_start AND $current_end\n"
        "),\n"
        "previous_period AS (\n"
        f'    SELECT {aggregation.value}("{metric}") AS previous_value\n'
        f"    FROM {DATASET_TABLE_NAME}\n"
        f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $previous_start AND $previous_end\n"
        ")\n"
        "SELECT current_value,\n"
        "       previous_value,\n"
        "       current_value - previous_value AS delta_value,\n"
        "       CASE\n"
        "           WHEN previous_value IS NULL OR previous_value = 0 THEN NULL\n"
        "           ELSE (current_value - previous_value) * 1.0 / previous_value\n"
        "       END AS delta_percent\n"
        "FROM current_period, previous_period\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_anomaly_explanation(metric: str, intent: Any, limit: int) -> CompiledQuery:
    if intent.date_range is None:
        raise QueryCompilationError("anomaly_explanation intent requires a validated date_range")

    params: dict[str, Any] = {"limit": limit}
    period = _resolve_comparison_period(intent.date_range)
    params.update(period)
    non_date_where = _build_where_clause(intent, params, include_date_range=False)
    sql = (
        "WITH anomaly_window AS (\n"
        f'    SELECT avg("{metric}") AS anomaly_value\n'
        f"    FROM {DATASET_TABLE_NAME}\n"
        f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $current_start AND $current_end\n"
        "),\n"
        "baseline_window AS (\n"
        f'    SELECT avg("{metric}") AS baseline_value\n'
        f"    FROM {DATASET_TABLE_NAME}\n"
        f"    {non_date_where} AND \"{intent.date_range.column}\" BETWEEN $previous_start AND $previous_end\n"
        ")\n"
        "SELECT anomaly_value,\n"
        "       baseline_value,\n"
        "       anomaly_value - baseline_value AS delta_value,\n"
        "       CASE\n"
        "           WHEN baseline_value IS NULL OR baseline_value = 0 THEN NULL\n"
        "           ELSE (anomaly_value - baseline_value) * 1.0 / baseline_value\n"
        "       END AS delta_percent\n"
        "FROM anomaly_window, baseline_window\n"
        "LIMIT $limit"
    )
    return CompiledQuery(sql=sql, params=params)


def _compile_clarification_required(chart_hint: str | None, limit: int) -> CompiledQuery:
    return CompiledQuery(
        sql=(
            "SELECT 'clarification_required' AS intent,\n"
            "       $chart_hint AS chart_hint\n"
            "LIMIT $limit"
        ),
        params={"chart_hint": chart_hint, "limit": limit},
    )


def _build_where_clause(intent: Any, params: dict[str, Any], *, include_date_range: bool = True) -> str:
    clauses: list[str] = []
    if include_date_range and intent.date_range is not None:
        clauses.append(_compile_date_range(intent.date_range, params))
    for index, filter_clause in enumerate(intent.filters):
        clauses.append(_compile_filter(filter_clause.column, filter_clause.operator, filter_clause.value, params, index))
    if not clauses:
        return "WHERE 1=1"
    return "WHERE " + " AND ".join(clauses)


def _compile_filter(
    column: str,
    operator: FilterOperator,
    value: Any,
    params: dict[str, Any],
    index: int,
) -> str:
    match operator:
        case FilterOperator.EQ:
            param_name = f"filter_{index}"
            params[param_name] = value
            return f'"{column}" = ${param_name}'
        case FilterOperator.NEQ:
            param_name = f"filter_{index}"
            params[param_name] = value
            return f'"{column}" != ${param_name}'
        case FilterOperator.GT:
            param_name = f"filter_{index}"
            params[param_name] = value
            return f'"{column}" > ${param_name}'
        case FilterOperator.LT:
            param_name = f"filter_{index}"
            params[param_name] = value
            return f'"{column}" < ${param_name}'
        case FilterOperator.BETWEEN:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise QueryCompilationError("between filters require a two-item list or tuple")
            start_name = f"filter_{index}_start"
            end_name = f"filter_{index}_end"
            params[start_name] = value[0]
            params[end_name] = value[1]
            return f'"{column}" BETWEEN ${start_name} AND ${end_name}'
        case FilterOperator.IN:
            if not isinstance(value, (list, tuple)) or len(value) == 0:
                raise QueryCompilationError("in filters require a non-empty list or tuple")
            placeholders: list[str] = []
            for item_index, item in enumerate(value):
                param_name = f"filter_{index}_{item_index}"
                params[param_name] = item
                placeholders.append(f"${param_name}")
            return f'"{column}" IN ({", ".join(placeholders)})'
        case _:
            raise QueryCompilationError(f"Unsupported validated filter operator '{operator.value}'")


def _compile_date_range(date_range: DateRange, params: dict[str, Any]) -> str:
    if date_range.preset is not None:
        return _preset_date_clause(date_range.column, date_range.preset)

    params["date_start"] = date_range.start
    params["date_end"] = date_range.end
    return f'"{date_range.column}" BETWEEN $date_start AND $date_end'


def _preset_date_clause(column: str, preset: str) -> str:
    mapping = {
        "today": f'"{column}" BETWEEN CURRENT_DATE AND CURRENT_DATE',
        "yesterday": f'"{column}" BETWEEN CURRENT_DATE - INTERVAL 1 DAY AND CURRENT_DATE - INTERVAL 1 DAY',
        "last_7_days": f'"{column}" BETWEEN CURRENT_DATE - INTERVAL 6 DAY AND CURRENT_DATE',
        "last_30_days": f'"{column}" BETWEEN CURRENT_DATE - INTERVAL 29 DAY AND CURRENT_DATE',
        "last_90_days": f'"{column}" BETWEEN CURRENT_DATE - INTERVAL 89 DAY AND CURRENT_DATE',
        "this_month": f'"{column}" BETWEEN date_trunc(\'month\', CURRENT_DATE) AND CURRENT_DATE',
        "last_month": f'"{column}" BETWEEN date_trunc(\'month\', CURRENT_DATE - INTERVAL 1 MONTH) AND date_trunc(\'month\', CURRENT_DATE) - INTERVAL 1 DAY',
        "this_year": f'"{column}" BETWEEN date_trunc(\'year\', CURRENT_DATE) AND CURRENT_DATE',
        "year_to_date": f'"{column}" BETWEEN date_trunc(\'year\', CURRENT_DATE) AND CURRENT_DATE',
    }
    try:
        return mapping[preset]
    except KeyError as exc:
        raise QueryCompilationError(f"Unsupported validated preset '{preset}'") from exc


def _resolve_time_granularity(date_range: DateRange | None) -> str:
    if date_range is None:
        return "day"
    if date_range.preset in {"this_year", "year_to_date"}:
        return "month"
    if date_range.preset in {"last_90_days", "this_month", "last_month"}:
        return "week"
    if date_range.start is None or date_range.end is None:
        return "day"
    span_days = (date.fromisoformat(date_range.end) - date.fromisoformat(date_range.start)).days
    if span_days >= 180:
        return "month"
    if span_days >= 31:
        return "week"
    return "day"


def _resolve_order_clause(intent: Any, *, default_column: str, default_direction: str) -> str:
    if intent.sort is None:
        return f"ORDER BY {default_column} {default_direction}"
    direction = "ASC" if intent.sort.direction == SortDirection.ASC else "DESC"
    if intent.sort.column in intent.group_by:
        return f'ORDER BY "{intent.sort.column}" {direction}'
    return f"ORDER BY {default_column} {direction}"


def _group_select(group_by: list[str]) -> str:
    return ", ".join(f'"{column}"' for column in group_by)


def _resolve_comparison_period(date_range: DateRange) -> dict[str, str]:
    if date_range.start is not None and date_range.end is not None:
        current_start = date.fromisoformat(date_range.start)
        current_end = date.fromisoformat(date_range.end)
        span_days = (current_end - current_start).days
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=span_days)
        return {
            "current_start": current_start.isoformat(),
            "current_end": current_end.isoformat(),
            "previous_start": previous_start.isoformat(),
            "previous_end": previous_end.isoformat(),
        }

    today = date.today()
    match date_range.preset:
        case "today":
            current_start = current_end = today
        case "yesterday":
            current_start = current_end = today - timedelta(days=1)
        case "last_7_days":
            current_start = today - timedelta(days=6)
            current_end = today
        case "last_30_days":
            current_start = today - timedelta(days=29)
            current_end = today
        case "last_90_days":
            current_start = today - timedelta(days=89)
            current_end = today
        case "this_month" | "last_month" | "this_year" | "year_to_date":
            raise QueryCompilationError(
                f"comparison/anomaly compilation for preset '{date_range.preset}' is not supported yet; use explicit dates"
            )
        case _:
            raise QueryCompilationError(f"Unsupported validated preset '{date_range.preset}'")

    span_days = (current_end - current_start).days
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=span_days)
    return {
        "current_start": current_start.isoformat(),
        "current_end": current_end.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
    }
