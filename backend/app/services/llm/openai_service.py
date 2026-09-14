from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger
from app.services.llm.base import BaseLLMService


class OpenAIService(BaseLLMService):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.default_model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        if not self.client or not self.api_key or self.api_key.startswith("your_"):
            return (
                "⚠️ **OpenAI API Key not configured.**\n\n"
                "To enable live OpenAI generation, please set `OPENAI_API_KEY` in your `.env` file.\n\n"
                "*(Tip: You can also switch to local Ollama by setting `LLM_PROVIDER=ollama` in `.env`)*"
            )

        target_model = model or self.default_model
        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise RuntimeError(f"OpenAI completion failed: {str(e)}")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client or not self.api_key or self.api_key.startswith("your_"):
            # Dummy embedding fallback for development without API key
            logger.warning("OpenAI API key missing, returning deterministic dummy vectors")
            return [[0.01 * (i + j) for j in range(1536)] for i in range(len(texts))]

        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise RuntimeError(f"OpenAI embedding failed: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        configured = bool(self.api_key and not self.api_key.startswith("your_"))
        return {
            "provider": "openai",
            "configured": configured,
            "default_model": self.default_model,
            "embedding_model": self.embedding_model,
            "status": "ready" if configured else "unconfigured_api_key",
        }
