from typing import List, Dict, Any, Optional
import httpx
from openai import AsyncOpenAI
from config.settings import settings, logger
from services.exceptions import LLMServiceError, InvalidProviderError


class LLMService:
    """Manages AI inference across OpenAI and Ollama providers."""

    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.ollama_model = settings.OLLAMA_MODEL

        self.openai_client = AsyncOpenAI(api_key=self.openai_key) if self.openai_key else None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Dict[str, str]:
        """
        Invoke the requested provider (OpenAI or Ollama).
        Returns a dict: {"content": response_text, "provider": provider_used, "model": model_used}
        """
        chosen_provider = (provider or settings.LLM_PROVIDER).lower().strip()

        if chosen_provider == "openai":
            content = await self._generate_openai(
                messages=messages,
                model=model or self.openai_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "content": content,
                "provider": "openai",
                "model": model or self.openai_model,
            }

        elif chosen_provider == "ollama":
            content = await self._generate_ollama(
                messages=messages,
                model=model or self.ollama_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "content": content,
                "provider": "ollama",
                "model": model or self.ollama_model,
            }

        else:
            raise InvalidProviderError(provider=chosen_provider)

    async def _generate_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if not self.openai_client or not self.openai_key or self.openai_key.startswith("your_"):
            return (
                "⚠️ **OpenAI API Key Not Configured**\n\n"
                "Please configure `OPENAI_API_KEY` in your `.env` file to enable live cloud generation.\n\n"
                "*Tip: You can also use offline local inference by switching to Ollama (`provider='ollama'`).*"
            )

        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise LLMServiceError(provider="openai", reason=str(e))

    async def _generate_ollama(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(f"{self.ollama_base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
                else:
                    raise LLMServiceError(
                        provider="ollama",
                        reason=f"HTTP {res.status_code}: {res.text}",
                    )
        except httpx.ConnectError:
            return (
                f"⚠️ **Could not connect to Ollama at `{self.ollama_base_url}`**\n\n"
                "Please ensure the Ollama service is active (`ollama serve`) and model is pulled (`ollama pull llama3`)."
            )
        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise LLMServiceError(provider="ollama", reason=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """Check status of configured LLM provider."""
        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai":
            configured = bool(self.openai_key and not self.openai_key.startswith("your_"))
            return {
                "provider": "openai",
                "status": "ready" if configured else "unconfigured_api_key",
                "default_model": self.openai_model,
            }
        else:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"{self.ollama_base_url}/api/tags")
                    if res.status_code == 200:
                        models = [m.get("name") for m in res.json().get("models", [])]
                        return {
                            "provider": "ollama",
                            "status": "ready",
                            "base_url": self.ollama_base_url,
                            "available_models": models,
                        }
            except Exception as e:
                return {
                    "provider": "ollama",
                    "status": "unreachable",
                    "error": str(e),
                }
            return {"provider": "ollama", "status": "unknown"}


_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
