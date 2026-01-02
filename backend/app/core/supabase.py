import os
from supabase import create_client, Client
from app.core.config import settings

# Log the configuration being used
print(f"\n{'='*70}")
print(f"SUPABASE CONFIGURATION AT STARTUP")
print(f"{'='*70}")
print(f"URL: {settings.SUPABASE_URL}")
print(f"Key: {settings.SUPABASE_KEY[:20]}...")
print(f"{'='*70}\n")

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Initialize Supabase admin client (with service role key)
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    """Get Supabase client instance."""
    return supabase


def get_supabase_admin() -> Client:
    """Get Supabase admin client instance (use with caution)."""
    return supabase_admin

