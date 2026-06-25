"""
AI Provider factory — returns the best available provider.
Priority: Gemini → OpenAI → Anthropic → Mock (always works, no API key required).
Business logic uses AITextProvider; swapping providers requires zero code changes.
"""
from .anthropic_provider import AnthropicProvider
from .base import AITextProvider
from .gemini_provider import GeminiProvider
from .mock import MockTextProvider
from .openai_provider import OpenAIProvider

__all__ = [
    "AITextProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "MockTextProvider",
    "get_provider",
    "get_provider_name",
]

_provider: AITextProvider | None = None


def get_provider() -> AITextProvider:
    global _provider
    if _provider is not None:
        return _provider

    from app.core.config import get_settings
    s = get_settings()

    if s.gemini_api_key:
        _provider = GeminiProvider(s.gemini_api_key)
    elif s.openai_api_key:
        _provider = OpenAIProvider(s.openai_api_key)
    elif s.anthropic_api_key:
        _provider = AnthropicProvider(s.anthropic_api_key)
    else:
        _provider = MockTextProvider()

    return _provider


def get_provider_name() -> str:
    return get_provider().name
