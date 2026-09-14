from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMService(ABC):
    """Abstract Base Class defining the LLM provider contract."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        """Generate conversational completion from a list of message dicts."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Verify provider availability and connection status."""
        pass
