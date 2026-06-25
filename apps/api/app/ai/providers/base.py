from abc import ABC, abstractmethod


class AITextProvider(ABC):
    """Abstract base for all AI text generation providers."""
    name: str = "unknown"

    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        ...

    def is_available(self) -> bool:
        return True
