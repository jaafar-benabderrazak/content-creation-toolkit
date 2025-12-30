import os
from supabase import create_client, Client
from app.core.config import settings

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

