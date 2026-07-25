from functools import lru_cache

from app.core.config import get_settings
from app.features.ai.provider import AIProvider, FallbackProvider, GeminiProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    """Use Gemini when a key is configured; fall back deterministically without one."""
    settings = get_settings()
    if settings.gemini_api_key:
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    return FallbackProvider()


@lru_cache
def get_fallback_provider() -> FallbackProvider:
    return FallbackProvider()
