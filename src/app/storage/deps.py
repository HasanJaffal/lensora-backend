from functools import lru_cache

from app.common.exceptions import StorageNotConfiguredError
from app.core.config import get_settings
from app.storage.client import ObjectStorage, SupabaseObjectStorage


@lru_cache
def get_object_storage() -> ObjectStorage:
    """The configured object store.

    Unlike the AI provider there is no meaningful fallback for storage — silently accepting an
    upload that is never persisted would lose the file — so a missing configuration surfaces as
    a typed 503 instead.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise StorageNotConfiguredError(
            "Supabase Storage is not configured; set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    return SupabaseObjectStorage(
        project_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        bucket=settings.supabase_storage_bucket,
    )
