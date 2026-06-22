import pytest
from app.nlq.context_resolver import resolve_context, resolve_fresh_question
from app.nlq.schemas import IntentType, SingleMetricIntent, GroupedMetricIntent, TimeSeriesIntent
from app.db.models import DatasetColumn

@pytest.fixture
def sample_columns():
    return [
        DatasetColumn.model_construct(name="order_date", display_name="Order Date", data_type="date", semantic_role="time"),
        DatasetColumn.model_construct(name="order_id", display_name="Order ID", data_type="string", semantic_role="identifier"),
        DatasetColumn.model_construct(name="revenue", display_name="Revenue", data_type="number", semantic_role="metric"),
        DatasetColumn.model_construct(name="region", display_name="Region", data_type="category", semantic_role="dimension", sample_values=["West", "East"]),
        DatasetColumn.model_construct(name="product_category", display_name="Product Category", data_type="category", semantic_role="dimension", sample_values=["Electronics", "Apparel"]),
        DatasetColumn.model_construct(name="marketing_channel", display_name="Marketing Channel", data_type="category", semantic_role="dimension", sample_values=["Paid Search", "Organic"]),
        DatasetColumn.model_construct(name="segment", display_name="Customer Segment", data_type="category", semantic_role="dimension", sample_values=["Returning", "New"]),
        DatasetColumn.model_construct(name="discount_percent", display_name="Discount Percent", data_type="number", semantic_role="dimension"),
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
    assert result.date_range is not None
    assert result.date_range.column == "order_date"
    assert result.date_range.preset == "last_30_days"

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


def test_resolve_context_break_down_handles_punctuation(sample_columns):
    prior = SingleMetricIntent(
        intent=IntentType.SINGLE_METRIC,
        metric="revenue",
        aggregation="sum"
    )

    result = resolve_context(prior, "Break that down by product category.", sample_columns)

    assert result != "treat_as_fresh"
    assert result.group_by == ["product_category"]


def test_resolve_fresh_question_orders_by_region(sample_columns):
    result = resolve_fresh_question("Show orders by region.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent == IntentType.GROUPED_METRIC
    assert result.metric == "order_id"
    assert result.aggregation.value == "count"
    assert result.group_by == ["region"]


def test_resolve_fresh_question_last_quarter(sample_columns):
    result = resolve_fresh_question("Revenue by product category last quarter.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent == IntentType.GROUPED_METRIC
    assert result.metric == "revenue"
    assert result.group_by == ["product_category"]
    assert result.date_range is not None
    assert result.date_range.preset == "last_quarter"


def test_resolve_fresh_question_average_order_value(sample_columns):
    result = resolve_fresh_question("Average order value by region.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent == IntentType.GROUPED_METRIC
    assert result.metric == "revenue"
    assert result.aggregation.value == "avg"


def test_resolve_fresh_question_discount_impact(sample_columns):
    result = resolve_fresh_question("Show discount impact on revenue.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent == IntentType.CORRELATION
    assert result.metric == "revenue"
    assert result.group_by == ["discount_percent"]


def test_resolve_fresh_question_plural_dimension_matching(sample_columns):
    result = resolve_fresh_question("Top 5 categories by revenue.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent == IntentType.TOP_N
    assert result.group_by == ["product_category"]


def test_resolve_fresh_question_dataset_summary(sample_columns):
    result = resolve_fresh_question("Summarize the dataset.", sample_columns)

    assert result != "defer_to_llm"
    assert result.intent in {IntentType.GROUPED_METRIC, IntentType.SINGLE_METRIC}
