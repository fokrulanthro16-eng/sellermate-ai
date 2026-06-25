"""
CampaignEngine — generates marketing campaign text using the configured AI provider.
Falls back to MockTextProvider when no API keys are set.
"""
from __future__ import annotations

from app.ai.providers import get_provider


SYSTEM_PROMPT = (
    "You are a top-tier Bangladeshi f-commerce marketing copywriter. "
    "Write engaging, concise campaign text. Match the requested language and tone exactly."
)


async def generate_campaign(
    campaign_type: str,
    product_name: str,
    product_price: str,
    language: str = "bn",
    tone: str = "friendly",
    extra_context: str = "",
) -> tuple[str, str]:
    """
    Returns (content, provider_name).
    campaign_type: 'fb_post' | 'fb_ad' | 'email' | 'sms'
    language: 'bn' | 'en'
    """
    provider = get_provider()

    type_map = {
        "fb_post": "Facebook Post",
        "fb_ad": "Facebook Ad",
        "email": "Email Campaign",
        "sms": "SMS Campaign",
    }
    type_label = type_map.get(campaign_type, campaign_type)
    lang_label = "বাংলায়" if language == "bn" else "in English"
    tone_label = tone

    user_prompt = (
        f"Write a {type_label} {lang_label} in a {tone_label} tone.\n"
        f"Product: {product_name}\n"
        f"Price: {product_price}\n"
        f"campaign_type: {campaign_type}\n"
        f"Language: {'বাংলা' if language == 'bn' else 'English'}\n"
    )
    if extra_context:
        user_prompt += f"Additional context: {extra_context}\n"

    content = await provider.complete(SYSTEM_PROMPT, user_prompt, max_tokens=600)
    return content, provider.name
