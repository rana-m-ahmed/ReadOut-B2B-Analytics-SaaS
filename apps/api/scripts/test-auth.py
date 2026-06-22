import os
import requests
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
r = c.auth.sign_in_with_password({'email': 'demo-8f110cec@example.com', 'password': 'Password123!'})
token = r.session.access_token
print("Token:", token[:15])
res = requests.get('http://localhost:8000/datasets', headers={'Authorization': f'Bearer {token}'})
print(res.status_code, res.text)
