import pytest
from app.nlq.context_resolver import resolve_context
from app.nlq.schemas import AnalyticsIntent, IntentType, SingleMetricIntent, GroupedMetricIntent, TimeSeriesIntent, IntentFilter, FilterOperator
from app.db.models import DatasetColumn

@pytest.fixture
def sample_columns():
    return [
        DatasetColumn.model_construct(name="revenue", display_name="Revenue", data_type="number", semantic_role="metric"),
        DatasetColumn.model_construct(name="region", display_name="Region", data_type="category", semantic_role="dimension"),
        DatasetColumn.model_construct(name="segment", display_name="Customer Segment", data_type="category", semantic_role="dimension", sample_values=["Returning", "New"]),
    ]

def test_resolve_context_break_down(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )
    result = resolve_context(prior, "break that down by region", sample_columns)
    
    assert result != "treat_as_fresh"
    assert result.intent == IntentType.GROUPED_METRIC
    assert result.metric == "revenue"
    assert result.group_by == ["region"]

def test_resolve_context_compare(sample_columns):
    prior = GroupedMetricIntent(
        intent=IntentType.GROUPED_METRIC,
        metric="revenue",
        aggregation="sum",
        group_by=["region"]
    )
    result = resolve_context(prior, "compare with previous period", sample_columns)
    
    assert result != "treat_as_fresh"
    assert result.intent == IntentType.COMPARISON
    assert result.metric == "revenue"
    assert result.group_by == ["region"]

def test_resolve_context_only_for_filter(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )
    result = resolve_context(prior, "only for returning customers", sample_columns)
    
    assert result != "treat_as_fresh"
    assert result.intent == IntentType.SINGLE_METRIC
    assert len(result.filters) == 1
    assert result.filters[0].column == "segment"
    assert result.filters[0].value == "Returning"

def test_resolve_context_show_as_chart_valid(sample_columns):
    prior = TimeSeriesIntent(
        intent=IntentType.TIME_SERIES,
        metric="revenue",
        aggregation="sum"
    )
    result = resolve_context(prior, "show as a line chart", sample_columns)
    
    assert result != "treat_as_fresh"
    assert result.intent == IntentType.TIME_SERIES
    assert result.chart_hint == "line"

def test_resolve_context_show_as_chart_invalid(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )
    # single_metric can only be metric_card, not line chart
    result = resolve_context(prior, "show as a line chart", sample_columns)
    
    assert result == "treat_as_fresh"

def test_resolve_context_what_caused_that(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )
    result = resolve_context(prior, "what caused that?", sample_columns)
    
    assert result != "treat_as_fresh"
    assert result.intent == IntentType.GROUPED_METRIC
    assert result.metric == "revenue"
    # region is the first dimension column in the fixture list
    assert result.group_by == ["region"]

def test_resolve_context_unmatched(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )
    result = resolve_context(prior, "can you give me a completely different dashboard?", sample_columns)
    
    assert result == "treat_as_fresh"
