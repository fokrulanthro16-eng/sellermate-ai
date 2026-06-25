from fastapi import APIRouter

router = APIRouter()

_DISPLAY_LABELS: dict[str, str] = {
    "gemini":    "Gemini",
    "openai":    "OpenAI",
    "anthropic": "Claude",
    "mock":      "Mock",
}


@router.get("/provider/status")
async def provider_status() -> dict:
    from app.ai.providers import get_provider_name
    name = get_provider_name()
    return {
        "active_provider": name,
        "display_label": _DISPLAY_LABELS.get(name, name.capitalize()),
        "is_mock": name == "mock",
    }
