import asyncio

from .base import AITextProvider


class GeminiProvider(AITextProvider):
    name = "gemini"
    _TIMEOUT = 30.0

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def is_available(self) -> bool:
        return bool(self._key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        from google import genai

        client = genai.Client(api_key=self._key)
        prompt = f"{system}\n\n{user}"
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content, "gemini-2.0-flash", prompt
                ),
                timeout=self._TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Gemini API did not respond within {self._TIMEOUT}s")
        return resp.text.strip() if resp.text else ""
