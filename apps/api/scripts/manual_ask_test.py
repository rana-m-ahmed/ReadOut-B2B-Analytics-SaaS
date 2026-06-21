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
        "What is the total revenue for the last 30 days?",
        "break that down by region",
        "compare with previous period",
        "show as a bar chart"
    ]
    
    print(f"Running session followup sequence... (Using Groq model {settings.GROQ_PRIMARY_MODEL})")
    
    session_id = None
    for i, q in enumerate(questions):
        print(f"\n[Q{i+1}] {q}")
        payload = {"dataset_id": str(demo_dataset.id), "question": q}
        if session_id:
            payload["session_id"] = session_id
            
        resp = client.post("/ask", json=payload, headers=headers, timeout=120.0)
        
        if resp.status_code == 200:
            data = resp.json()
            if session_id is None:
                session_id = data.get("session_id")
                print(f"-> Set session_id: {session_id}")
            print(f"-> Status: 200 OK")
            if data.get("clarification_required"):
                print(f"-> Clarification: {data['clarification_required']}")
            else:
                print(f"-> Summary: {data['summary']}")
                print(f"-> Intent: {data['query_plan']['intent']}")
                if data.get("chart"):
                    print(f"-> Chart Type: {data['chart']['type']}")
                print(f"-> Suggested followups: {data.get('suggested_followups')}")
        else:
            print(f"-> Failed: {resp.status_code} {resp.text}")

    # Cleanup
    workspace_repo.delete(user_id, workspace.id)
    supabase.auth.admin.delete_user(user_id)

if __name__ == "__main__":
    asyncio.run(main())
