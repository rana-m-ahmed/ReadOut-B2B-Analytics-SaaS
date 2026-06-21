"""Supabase service-role client access.

This module is the only approved choke point for the service-role client.
Route handlers and non-repository modules must not import the client directly.
"""

from __future__ import annotations

from supabase import Client, create_client

from app.core.config import get_settings

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Return the cached service-role Supabase client."""
    global _supabase_client

    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


def reset_supabase_client() -> None:
    """Reset the cached client for tests."""
    global _supabase_client
    _supabase_client = None
