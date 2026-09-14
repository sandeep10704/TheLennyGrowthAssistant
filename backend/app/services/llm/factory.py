from typing import Optional
from app.core.config import settings
from app.services.llm.base import BaseLLMService
from app.services.llm.openai_service import OpenAIService
from app.services.llm.ollama_service import OllamaService

_openai_instance: Optional[OpenAIService] = None
_ollama_instance: Optional[OllamaService] = None


def get_llm_service(provider: Optional[str] = None) -> BaseLLMService:
    """
    Factory function to retrieve the configured LLM service.
    Supports overriding provider per-request ('openai' or 'ollama').
    """
    global _openai_instance, _ollama_instance

    target_provider = (provider or settings.LLM_PROVIDER).lower().strip()

    if target_provider == "ollama":
        if _ollama_instance is None:
            _ollama_instance = OllamaService()
        return _ollama_instance
    else:
        # Default to OpenAI
        if _openai_instance is None:
            _openai_instance = OpenAIService()
        return _openai_instance
