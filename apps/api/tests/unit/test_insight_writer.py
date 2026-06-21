import pytest
from app.insights.schemas import InsightCandidate
from app.insights.insight_writer import write_insights
from app.core.config import get_settings

@pytest.mark.anyio
async def test_insight_writer_live(live_env, monkeypatch):
    for k, v in live_env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    
    settings = get_settings()
    
    c1 = InsightCandidate(
        insight_type="mom_growth",
        metric_name="revenue",
        dimension_name="order_date",
        primary_value=123456.78,
        percent_change=0.152
    )
    
    candidates = [c1]
    res = await write_insights(candidates, settings)
    
    assert len(res) == 1
    assert res[0].text is not None
    
    # Must contain the exact numbers
    assert "123.5k" in res[0].text
    assert "15.2%" in res[0].text
