import pytest
import httpx
from app.anomalies.schemas import Anomaly
from app.anomalies.anomaly_explainer import explain_anomaly
from app.core.config import get_settings

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        
    def json(self):
        return self._json

@pytest.mark.anyio
async def test_anomaly_explainer_mocked_safe(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "mock-key")
    
    async def mock_post_safe(*args, **kwargs):
        return MockResponse({
            "choices": [{
                "message": {
                    "content": "Revenue was lower than expected, worth checking."
                }
            }]
        })
        
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_safe)
    
    a = Anomaly(
        detector_type="zscore",
        date="2025-04-20",
        metric_name="revenue",
        dimension_name="region",
        dimension_value="West",
        actual_value=1000,
        expected_value=2000,
        severity=-3.1
    )
    
    res = await explain_anomaly(a, settings)
    assert res.explanation == "Revenue was lower than expected, worth checking."

@pytest.mark.anyio
async def test_anomaly_explainer_mocked_alarmist(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "mock-key")
    
    async def mock_post_alarmist(*args, **kwargs):
        return MockResponse({
            "choices": [{
                "message": {
                    "content": "Revenue has suffered a critical crash and is completely broken."
                }
            }]
        })
        
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_alarmist)
    
    a = Anomaly(
        detector_type="zscore",
        date="2025-04-20",
        metric_name="revenue",
        dimension_name="region",
        dimension_value="West",
        actual_value=1000,
        expected_value=2000,
        severity=-3.1
    )
    
    res = await explain_anomaly(a, settings)
    # The blocklist should trigger and it should fallback to a safe string
    assert "critical" not in res.explanation
    assert "broken" not in res.explanation
    assert "crash" not in res.explanation
    assert "Unusual revenue observed on 2025-04-20" in res.explanation
