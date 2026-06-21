import asyncio
import logging
from uuid import uuid4
from fastapi.testclient import TestClient
from pathlib import Path

# Setup logging to see the fallback in action
logging.basicConfig(level=logging.WARNING)

from app.main import create_app
from app.db.repositories import DatasetRepository, WorkspaceRepository
from app.core.config import get_settings
from app.db.models import WorkspaceCreate
import jwt
from datetime import datetime, timedelta, timezone

def _build_auth_token(secret: str, user_id: str) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": False},
        },
        secret,
        algorithm="HS256",
    )

async def main():
    app = create_app()
    client = TestClient(app)
    
    settings = get_settings()
    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    supabase = workspace_repo._client
    
    demo_dataset = dataset_repo.get_demo_dataset()
    if not demo_dataset:
        print("Demo dataset missing!")
        return

    # Create temporary user for test
    email = f"manual-test-{uuid4().hex}@example.com"
    password = f"T3st!{uuid4().hex}"
    user_response = supabase.auth.admin.create_user({"email": email, "password": password, "email_confirm": True})
    user_id = user_response.user.id
    
    workspace = workspace_repo.create(
        user_id,
        WorkspaceCreate(name="Manual Test", slug=f"manual-{uuid4().hex[:8]}")
    )
    
    token = _build_auth_token(settings.SUPABASE_JWT_SECRET, user_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    questions = [
        "What is the total revenue?",
        "Show me sales by region.",
        "How did revenue trend over the last 6 months?",
        "What is the correlation between discount and revenue?",
        "Who are the top 5 customers?",
        "Explain any anomalies in revenue.",
        "Compare revenue this month to last month.",
        "What is the proportion of revenue by segment?",
        "Show me bottom 3 products.",
        "What is the total discount given?"
    ]
    
    print(f"Running 10 questions against /ask... (Using Groq model {settings.GROQ_PRIMARY_MODEL})")
    
    for i, q in enumerate(questions):
        print(f"\n[Q{i+1}] {q}")
        resp = client.post("/ask", json={"dataset_id": str(demo_dataset.id), "question": q}, headers=headers, timeout=120.0)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"-> Status: 200 OK")
            if data.get("clarification_required"):
                print(f"-> Clarification: {data['clarification_required']}")
            else:
                print(f"-> Summary: {data['summary']}")
                if data.get("chart"):
                    print(f"-> Chart Type: {data['chart']['type']}")
        else:
            print(f"-> Failed: {resp.status_code} {resp.text}")

    # Cleanup
    workspace_repo.delete(user_id, workspace.id)
    supabase.auth.admin.delete_user(user_id)

if __name__ == "__main__":
    asyncio.run(main())
