import pytest
import httpx
from app.insights.schemas import InsightCandidate
from app.insights.insight_writer import write_insights
from app.core.config import get_settings

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        
    def json(self):
        return self._json

@pytest.mark.anyio
async def test_insight_writer_mocked(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "mock-key")
    
    # Track the prompt sent to the LLM
    captured_prompt = None
    
    async def mock_post(*args, **kwargs):
        nonlocal captured_prompt
        captured_prompt = kwargs.get("json", {}).get("messages", [])[1]["content"]
        
        # The mock returns a string that just echoes back the exact numbers it was given
        return MockResponse({
            "choices": [{
                "message": {
                    "content": "Revenue grew by 15.2% to 123.5k."
                }
            }]
        })
        
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    c1 = InsightCandidate(
        insight_type="mom_growth",
        metric_name="revenue",
        dimension_name="order_date",
        primary_value=123456.78,
        percent_change=0.152
    )
    
    res = await write_insights([c1], settings)
    
    assert len(res) == 1
    assert res[0].text is not None
    
    # Must contain the exact numbers from the mock response
    assert "123.5k" in res[0].text
    assert "15.2%" in res[0].text
    
    # And verify the exact numbers were actually in the prompt we built
    assert "123.5k" in captured_prompt
    assert "15.2%" in captured_prompt
