import asyncio

from .base import AITextProvider


class GeminiProvider(AITextProvider):
    name = "gemini"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def is_available(self) -> bool:
        return bool(self._key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        from google import genai
        client = genai.Client(api_key=self._key)
        prompt = f"{system}\n\n{user}"
        resp = await asyncio.to_thread(
            client.models.generate_content, "gemini-2.0-flash", prompt
        )
        return resp.text.strip() if resp.text else ""
