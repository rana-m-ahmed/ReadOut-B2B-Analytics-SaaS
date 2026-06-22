import os
import sys
import uuid
from pathlib import Path

# Add the parent directory to sys.path to allow imports from app
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from app.db.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    dummy_email = f"demo-{uuid.uuid4().hex[:8]}@example.com"
    dummy_password = "Password123!"
    
    # Create user with auto-confirmed email using admin API
    user_response = supabase.auth.admin.create_user(
        {
            "email": dummy_email,
            "password": dummy_password,
            "email_confirm": True,
        }
    )
    
    print(f"EMAIL={dummy_email}")
    print(f"PASSWORD={dummy_password}")

if __name__ == "__main__":
    main()
