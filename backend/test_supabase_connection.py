import os
from supabase import create_client

# Load from .env
from dotenv import load_dotenv
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Testing connection to: {url}")

try:
    supabase = create_client(url, key)
    
    # Try to query users table
    result = supabase.table("users").select("id").limit(1).execute()
    
    print("SUCCESS! Connected to Supabase")
    print(f"Users table exists: {result is not None}")
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\nPossible issues:")
    print("1. Database schema not run (run database_schema_replit.sql)")
    print("2. Wrong API keys in .env file")
    print("3. Network/firewall blocking Supabase")

