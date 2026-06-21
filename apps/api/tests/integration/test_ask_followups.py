import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from pathlib import Path

API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

@pytest.fixture(scope="module")
def live_env():
    return _load_env_file(API_ENV_FILE)

@pytest.mark.anyio
async def test_ask_followups_live(live_env, monkeypatch: pytest.MonkeyPatch):
    from app.core.config import get_settings
    from app.db.supabase_client import reset_supabase_client
    
    # We must reset and apply settings
    for k, v in live_env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    reset_supabase_client()
    
    from app.main import create_app
    app = create_app()
    client = TestClient(app)
    
    from app.db.repositories import WorkspaceRepository, DatasetRepository
    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    supabase = workspace_repo._client
    
    demo_dataset = dataset_repo.get_demo_dataset()
    if not demo_dataset:
        pytest.skip("Demo dataset not seeded. Run scripts/generate-demo-dataset.py and test_demo_seed_live.py first.")
    
    # We create a user for auth
    try:
        email = f"test-ask-followups-{uuid4().hex}@example.com"
        password = f"T3st!{uuid4().hex}"
        user_response = supabase.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        user_id = UUID(user_response.user.id)
        
        # Build token
        import jwt
        from datetime import datetime, timedelta, timezone
        token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "app_metadata": {"is_anonymous": False},
            },
            live_env["SUPABASE_JWT_SECRET"],
            algorithm="HS256",
        )
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        from app.db.models import WorkspaceCreate
        workspace = workspace_repo.create(
            user_id,
            WorkspaceCreate(name="Routes Ask Followups", slug=f"routes-ask-follow-{uuid4().hex[:8]}"),
        )
        workspace_id = workspace.id
        
        dataset_id = demo_dataset.id

        # Turn 1: Fresh Question
        resp1 = client.post(
            "/ask",
            json={"dataset_id": str(dataset_id), "question": "What is the total revenue for the last 30 days?"},
            headers=auth_headers,
            timeout=120.0,
        )
        assert resp1.status_code == 200, resp1.text
        data1 = resp1.json()
        
        if data1.get("chart") is None and data1.get("summary", "").startswith("I'm having trouble connecting"):
            pytest.skip("Groq completely rate-limited during initial question; skipping remainder of test")
            
        assert data1["query_plan"]["intent"] == "single_metric"
        assert data1["query_plan"]["metric"] == "revenue"
        session_id = data1["session_id"]
        assert session_id is not None
        
        # Turn 2: "break that down by region"
        resp2 = client.post(
            "/ask",
            json={"dataset_id": str(dataset_id), "question": "break that down by region", "session_id": session_id},
            headers=auth_headers,
            timeout=120.0,
        )
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()
        assert data2["query_plan"]["intent"] == "grouped_metric"
        assert data2["query_plan"]["metric"] == "revenue"
        assert data2["query_plan"]["group_by"] == ["region"]
        assert data2["chart"]["type"] in ["bar", "donut"]
        
        # Turn 3: "compare with previous period"
        resp3 = client.post(
            "/ask",
            json={"dataset_id": str(dataset_id), "question": "compare with previous period", "session_id": session_id},
            headers=auth_headers,
            timeout=120.0,
        )
        assert resp3.status_code == 200, resp3.text
        data3 = resp3.json()
        assert data3["query_plan"]["intent"] == "comparison"
        assert data3["query_plan"]["metric"] == "revenue"
        assert data3["query_plan"]["group_by"] == ["region"]
        
        # Turn 4: "show as a bar chart"
        resp4 = client.post(
            "/ask",
            json={"dataset_id": str(dataset_id), "question": "show as a bar chart", "session_id": session_id},
            headers=auth_headers,
            timeout=120.0,
        )
        assert resp4.status_code == 200, resp4.text
        data4 = resp4.json()
        assert data4["query_plan"]["intent"] == "comparison"
        assert data4["query_plan"]["chart_hint"] == "bar"
        
        # Check that followups were generated
        assert len(data4.get("suggested_followups", [])) > 0
        
    finally:
        # cleanup user
        try:
            supabase.auth.admin.delete_user(str(user_id))
        except Exception:
            pass
