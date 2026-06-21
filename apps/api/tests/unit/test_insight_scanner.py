import pytest
from app.db.repositories import WorkspaceRepository, DatasetRepository, DatasetColumnRepository
from app.insights.insight_scanner import scan_dataset_insights
from app.core.config import get_settings
from uuid import uuid4

@pytest.mark.anyio
async def test_scan_insights_live(live_env, monkeypatch):
    from app.db.supabase_client import reset_supabase_client
    
    for k, v in live_env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    reset_supabase_client()
    
    settings = get_settings()
    dataset_repo = DatasetRepository()
    col_repo = DatasetColumnRepository()
    
    demo_dataset = dataset_repo.get_demo_dataset()
    if not demo_dataset:
        pytest.skip("Demo dataset not seeded.")
        
    columns = col_repo.list_for_dataset(demo_dataset.workspace_id, demo_dataset.id)
    
    candidates = scan_dataset_insights(demo_dataset.workspace_id, demo_dataset.id, columns, settings)
    
    assert len(candidates) > 0
    
    types = {c.insight_type for c in candidates}
    assert "mom_growth" in types
    assert "top_category" in types
    assert "customer_mix" in types
    assert "region_contribution" in types
    
    # Check that payloads are well formed
    for c in candidates:
        assert c.chart_payload is not None
        assert "type" in c.chart_payload
        assert c.chart_payload["type"] in ("line", "bar", "donut")
