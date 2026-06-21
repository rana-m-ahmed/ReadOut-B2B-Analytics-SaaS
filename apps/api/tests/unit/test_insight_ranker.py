import pytest
from app.insights.schemas import InsightCandidate
from app.insights.insight_ranker import rank_insights

def test_insight_ranker():
    c1 = InsightCandidate(
        insight_type="mom_growth",
        metric_name="revenue",
        dimension_name="date",
        primary_value=50000,
        percent_change=0.20
    )
    
    c2 = InsightCandidate(
        insight_type="top_category",
        metric_name="units",
        dimension_name="product",
        primary_value=500,
        percent_change=None
    )
    
    c3 = InsightCandidate(
        insight_type="mom_growth",
        metric_name="revenue",
        dimension_name="date",
        primary_value=50000,
        percent_change=0.005 # too obvious
    )
    
    candidates = [c1, c2, c3]
    ranked = rank_insights(candidates, history_types={"top_category"})
    
    assert ranked[0].insight_type == "mom_growth"
    assert ranked[0].score == 5 # +3 (business impact) + 2 (high change)
    
    # c3 gets +3 (impact) - 1 (too obvious) = 2
    # c2 gets +2 (top category) - 1 (seen) = 1
    assert ranked[1] == c3
    assert ranked[2] == c2
