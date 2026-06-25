import asyncio
from .base import AITextProvider


class OpenAIProvider(AITextProvider):
    name = "openai"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def is_available(self) -> bool:
        return bool(self._key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        import openai
        client = openai.OpenAI(api_key=self._key)
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = resp.choices[0].message.content if resp.choices else ""
        return text.strip() if text else ""
