from functools import lru_cache

from app.core.config import get_settings
from app.features.ai.provider import AIProvider, AnthropicProvider, FallbackProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    """Select the AI strategy from settings; fall back deterministically without a key."""
    settings = get_settings()
    if settings.ai_api_key and settings.ai_provider.lower() == "anthropic":
        return AnthropicProvider(api_key=settings.ai_api_key, model=settings.ai_model)
    return FallbackProvider()


@lru_cache
def get_fallback_provider() -> FallbackProvider:
    return FallbackProvider()
