import asyncio

from .base import AITextProvider


class AnthropicProvider(AITextProvider):
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def is_available(self) -> bool:
        return bool(self._key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self._key)
        msg = await asyncio.to_thread(
            client.messages.create,
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text.strip() if msg.content else ""
