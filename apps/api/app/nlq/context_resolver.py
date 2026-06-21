import re
from typing import Literal

from app.nlq.schemas import (
    AnalyticsIntent,
    IntentType,
    IntentFilter,
    FilterOperator,
)
from app.db.models import DatasetColumn

def _get_valid_charts(intent: IntentType) -> set[str]:
    return {
        IntentType.SINGLE_METRIC: {"metric_card"},
        IntentType.TIME_SERIES: {"line", "bar", "multi_line"},
        IntentType.GROUPED_METRIC: {"bar", "donut", "table"},
        IntentType.PROPORTION: {"donut", "table"},
        IntentType.TOP_N: {"bar", "table"},
        IntentType.BOTTOM_N: {"bar", "table"},
        IntentType.CORRELATION: {"scatter", "table"},
        IntentType.COMPARISON: {"metric_card", "bar", "table"},
        IntentType.ANOMALY_EXPLANATION: {"line_with_highlighted_point", "table"}
    }.get(intent, {"table"})

def resolve_context(
    prior_intent: AnalyticsIntent,
    new_question: str,
    dataset_columns: list[DatasetColumn]
) -> AnalyticsIntent | Literal["treat_as_fresh"]:
    """
    Deterministically merge a follow-up question into a prior intent using fixed patterns.
    If it doesn't match a known pattern, return 'treat_as_fresh' to route it to the LLM.
    """
    question_lower = new_question.lower().strip()
    
    # Pattern 1: "break that down by X" or "break down by X"
    match_breakdown = re.search(r'(?:break that down by|break down by)\s+(.+)', question_lower)
    if match_breakdown:
        col_name = match_breakdown.group(1).strip()
        matched_col = None
        for col in dataset_columns:
            if col.name.lower() == col_name or (col.display_name and col.display_name.lower() == col_name):
                matched_col = col
                break
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
        return analytics_intent_adapter.validate_python(intent_dict)
        
    # Pattern 3: "only for returning customers" -> filter
    match_filter = re.search(r'only for\s+(.+)', question_lower)
    if match_filter:
        val_str = match_filter.group(1).strip()
        for col in dataset_columns:
            if not col.sample_values:
                continue
            for sample in col.sample_values:
                if sample is not None and str(sample).lower() in val_str:
                    new_intent = prior_intent.model_copy(deep=True)
                    new_intent.filters.append(IntentFilter(
                        column=col.name,
                        operator=FilterOperator.EQ,
                        value=sample
                    ))
                    return new_intent

    # Pattern 4: "show as a X chart"
    match_chart = re.search(r'show as a\s+(\w+(?:_with_highlighted_point)?)\s*chart', question_lower)
    if match_chart:
        chart_type = match_chart.group(1).strip()
        valid_charts = _get_valid_charts(prior_intent.intent)
        if chart_type in valid_charts:
            new_intent = prior_intent.model_copy(deep=True)
            new_intent.chart_hint = chart_type
            return new_intent
        # If the chart is invalid for the shape, we fall through to treat_as_fresh
            
    # Pattern 5: "what caused that?" -> ranked-breakdown candidate
    if "what caused that" in question_lower or "why did" in question_lower:
        candidates = [c for c in dataset_columns if c.semantic_role == "dimension" or c.data_type == "category"]
        if candidates:
            # Just pick the first dimension since we don't have unique_count in DatasetColumn
            best_col = candidates[0]
            from app.nlq.schemas import analytics_intent_adapter
            intent_dict = prior_intent.model_dump(exclude_none=True)
            intent_dict["intent"] = IntentType.GROUPED_METRIC.value
            intent_dict["group_by"] = [best_col.name]
            return analytics_intent_adapter.validate_python(intent_dict)

    return "treat_as_fresh"
