import pytest
from app.db.repositories import DatasetRepository, DatasetColumnRepository
from app.anomalies.zscore_detector import detect_zscore_anomalies
from app.anomalies.isolation_forest_detector import detect_isolation_forest_anomalies
from app.core.config import get_settings

@pytest.mark.anyio
async def test_anomaly_detectors_live(live_env, monkeypatch):
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
    
    # 1. Z-Score
    z_anomalies = detect_zscore_anomalies(demo_dataset.workspace_id, demo_dataset.id, columns, settings, threshold=3.0)
    
    # The seeded anomaly is 2025-04-14 through 2025-04-20 in West / Electronics
    # We should find at least one day in that window flagged for West / Electronics
    found_seeded = False
    for a in z_anomalies:
        if a.dimension_name == "region / product_category" and a.dimension_value == "West / Electronics":
            if "2025-04-14" <= a.date[:10] <= "2025-04-20":
                found_seeded = True
                break
    
    assert found_seeded, "Z-Score detector failed to flag the seeded West/Electronics anomaly"
    
    # 2. Isolation Forest
    if_anomalies = detect_isolation_forest_anomalies(demo_dataset.workspace_id, demo_dataset.id, columns, settings)
    # Isolation forest should flag at least something in the dataset (multivariate outliers exist in 20k rows)
    assert len(if_anomalies) > 0
    assert if_anomalies[0].detector_type == "isolation_forest"
