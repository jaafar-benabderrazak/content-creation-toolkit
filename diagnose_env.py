# Quick diagnostic script
import sys
sys.path.insert(0, 'C:\\Users\\Utilisateur\\projects\\librework\\librework\\backend')

from dotenv import load_dotenv
import os

# Load .env
env_path = 'C:\\Users\\Utilisateur\\projects\\librework\\librework\\backend\\.env'
load_dotenv(env_path)

print("="*70)
print("ENVIRONMENT VARIABLES CHECK")
print("="*70)
print(f"SUPABASE_URL from env: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY exists: {os.getenv('SUPABASE_KEY') is not None}")
print()

# Now check what settings.py loads
from app.core.config import settings
print("="*70)
print("SETTINGS MODULE CHECK")
print("="*70)
print(f"settings.SUPABASE_URL: {settings.SUPABASE_URL}")
print(f"settings.SUPABASE_KEY exists: {settings.SUPABASE_KEY is not None}")
print()

# Test connection
from supabase import create_client
print("="*70)
print("CONNECTION TEST")
print("="*70)
try:
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    result = client.table("users").select("count").limit(1).execute()
    print(f"SUCCESS! Connected to {settings.SUPABASE_URL}")
except Exception as e:
    print(f"FAILED: {e}")

