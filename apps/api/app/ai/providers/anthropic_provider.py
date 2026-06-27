import asyncio

from .base import AITextProvider


class AnthropicProvider(AITextProvider):
    name = "anthropic"
    _TIMEOUT = 30.0

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def is_available(self) -> bool:
        return bool(self._key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._key)
        try:
            msg = await asyncio.wait_for(
                asyncio.to_thread(
                    client.messages.create,
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                ),
                timeout=self._TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Anthropic API did not respond within {self._TIMEOUT}s")
        return msg.content[0].text.strip() if msg.content else ""
