import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from openai import AsyncOpenAI
from config.settings import settings, logger
from services.exceptions import (
    LLMServiceError,
    LLMTimeoutError,
    InvalidProviderError,
)

DEFAULT_SYSTEM_TEMPLATE = """You are Lenny Growth Assistant, an executive product & growth advisor modeled after Lenny Rachitsky's product frameworks, newsletter, and podcast interviews.

Your goal is to provide insightful, highly tactical, structured, and actionable guidance for founders, product leaders, and growth practitioners.

GROUNDING RULES:
1. Ground your advice directly in the provided context excerpts from Lenny's interviews and playbooks.
2. If the context contains specific metrics, benchmarks, or frameworks (e.g., Sean Ellis 40% PMF test, retention curves, Aha! moments, 4 growth loops), cite them clearly.
3. If the context doesn't contain the complete answer, apply sound first-principles product thinking while acknowledging context limits.
4. Structure your response with clear headings, bullet points, and key takeaways.

--- RETRIEVED TRANSCRIPT & PLAYBOOK CONTEXT ---
{context}
-----------------------------------------------
"""


# ==============================================================================
# Base Provider Interface
# ==============================================================================
class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers (OpenAI, Ollama, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: float = 30.0,
    ) -> str:
        """Generates text completion given a list of message dicts."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Verifies connectivity and model availability."""
        pass


# ==============================================================================
# 1. OpenAI Provider
# ==============================================================================
class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.default_model = settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: float = settings.LLM_TIMEOUT_SECONDS,
    ) -> str:
        if not self.client or not self.api_key or self.api_key.startswith("your_"):
            raise LLMServiceError(
                provider="openai",
                reason="OPENAI_API_KEY is not configured in environment.",
            )

        target_model = model or self.default_model
        try:
            # Wrap with explicit asyncio timeout handling
            async with asyncio.timeout(timeout):
                response = await self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,  # type: ignore
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""

        except asyncio.TimeoutError:
            logger.error(f"[OpenAIProvider] Generation timed out after {timeout}s.")
            raise LLMTimeoutError(provider="openai", timeout_seconds=timeout)
        except LLMTimeoutError:
            raise
        except Exception as e:
            logger.error(f"[OpenAIProvider] Invocation failed: {e}")
            raise LLMServiceError(provider="openai", reason=str(e))

    async def health_check(self) -> Dict[str, Any]:
        configured = bool(self.api_key and not self.api_key.startswith("your_"))
        return {
            "provider": "openai",
            "status": "ready" if configured else "unconfigured_api_key",
            "default_model": self.default_model,
        }


# ==============================================================================
# 2. Ollama Provider (Local)
# ==============================================================================
class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: float = settings.OLLAMA_TIMEOUT_SECONDS,
    ) -> str:
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with asyncio.timeout(timeout):
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.post(f"{self.base_url}/api/chat", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        return data.get("message", {}).get("content", "")
                    else:
                        raise LLMServiceError(
                            provider="ollama",
                            reason=f"HTTP {res.status_code}: {res.text}",
                        )

        except (asyncio.TimeoutError, httpx.TimeoutException):
            logger.error(f"[OllamaProvider] Local request timed out after {timeout}s.")
            raise LLMTimeoutError(provider="ollama", timeout_seconds=timeout)
        except httpx.ConnectError:
            raise LLMServiceError(
                provider="ollama",
                reason=f"Cannot connect to local Ollama daemon at {self.base_url}. Ensure 'ollama serve' is running.",
            )
        except (LLMServiceError, LLMTimeoutError):
            raise
        except Exception as e:
            logger.error(f"[OllamaProvider] Request failed: {e}")
            raise LLMServiceError(provider="ollama", reason=str(e))

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {
                        "provider": "ollama",
                        "status": "ready",
                        "base_url": self.base_url,
                        "available_models": models,
                    }
        except Exception as e:
            return {
                "provider": "ollama",
                "status": "unreachable",
                "base_url": self.base_url,
                "error": str(e),
            }
        return {"provider": "ollama", "status": "unknown"}


# ==============================================================================
# 3. LLM Service Layer (Config Switching, Timeouts & Fallback)
# ==============================================================================
class LLMService:
    """
    Unified LLM service layer with:
    - Config-based switching between OpenAI and Ollama
    - Common provider interface
    - Timeout handling
    - Automatic fallback logic if the primary provider fails
    """

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "ollama": OllamaProvider(),
        }

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Resolves provider by name or falls back to system configuration."""
        provider_name = (name or settings.LLM_PROVIDER).lower().strip()
        if provider_name not in self.providers:
            raise InvalidProviderError(provider=provider_name)
        return self.providers[provider_name]

    def _get_fallback_provider_name(self, primary: str) -> str:
        """Determines the secondary fallback provider."""
        return "ollama" if primary.lower() == "openai" else "openai"

    async def generate_response(
        self,
        query: str,
        context: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: Optional[float] = None,
        enable_fallback: Optional[bool] = None,
        system_template: Optional[str] = None,
    ) -> str:
        """
        Primary interface method required by the user specification:
        generate_response(query, context)

        Constructs context-grounded prompt, invokes configured provider with
        timeout protection, and automatically falls back to secondary provider if needed.
        """
        primary_name = (provider or settings.LLM_PROVIDER).lower().strip()
        fallback_allowed = enable_fallback if enable_fallback is not None else settings.LLM_FALLBACK_ENABLED

        # Construct prompt messages
        template = system_template or DEFAULT_SYSTEM_TEMPLATE
        system_content = template.format(context=context or "No specific transcript context provided.")

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
        ]

        # 1. Attempt generation with Primary Provider
        timeout_val = timeout or (
            settings.LLM_TIMEOUT_SECONDS if primary_name == "openai" else settings.OLLAMA_TIMEOUT_SECONDS
        )

        try:
            primary_provider = self.get_provider(primary_name)
            logger.info(f"Generating response using primary LLM provider '{primary_name}' (timeout={timeout_val}s)...")
            return await primary_provider.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                timeout=timeout_val,
            )

        except (LLMServiceError, LLMTimeoutError, Exception) as primary_exc:
            if not fallback_allowed:
                raise primary_exc

            # 2. Automatic Fallback Logic
            fallback_name = self._get_fallback_provider_name(primary_name)
            fallback_timeout = settings.OLLAMA_TIMEOUT_SECONDS if fallback_name == "ollama" else settings.LLM_TIMEOUT_SECONDS

            logger.warning(
                f"⚠️ Primary provider '{primary_name}' failed ({primary_exc}). "
                f"Triggering automatic fallback to '{fallback_name}' (timeout={fallback_timeout}s)..."
            )

            try:
                fallback_provider = self.get_provider(fallback_name)
                fallback_response = await fallback_provider.generate(
                    messages=messages,
                    temperature=temperature,
                    timeout=fallback_timeout,
                )
                return fallback_response

            except Exception as fallback_exc:
                logger.error(f"❌ Both primary '{primary_name}' and fallback '{fallback_name}' providers failed.")
                raise LLMServiceError(
                    provider=f"{primary_name}->{fallback_name}",
                    reason=(
                        f"Primary '{primary_name}' failed: {str(primary_exc)} | "
                        f"Fallback '{fallback_name}' failed: {str(fallback_exc)}"
                    ),
                )

    async def generate_chat_turn(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: Optional[float] = None,
        enable_fallback: bool = True,
    ) -> Dict[str, str]:
        """
        Executes a multi-turn chat sequence with fallback and timeout handling.
        Returns a dict: {"content": str, "provider": str, "model": str, "fallback_used": bool}
        """
        primary_name = (provider or settings.LLM_PROVIDER).lower().strip()
        timeout_val = timeout or (
            settings.LLM_TIMEOUT_SECONDS if primary_name == "openai" else settings.OLLAMA_TIMEOUT_SECONDS
        )

        try:
            p = self.get_provider(primary_name)
            content = await p.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                timeout=timeout_val,
            )
            return {
                "content": content,
                "provider": primary_name,
                "model": model or getattr(p, "default_model", "default"),
                "fallback_used": False,
            }
        except Exception as e:
            if not enable_fallback or not settings.LLM_FALLBACK_ENABLED:
                raise e

            fallback_name = self._get_fallback_provider_name(primary_name)
            logger.warning(f"Primary '{primary_name}' error ({e}), executing fallback to '{fallback_name}'...")
            try:
                fb = self.get_provider(fallback_name)
                fb_timeout = settings.OLLAMA_TIMEOUT_SECONDS if fallback_name == "ollama" else settings.LLM_TIMEOUT_SECONDS
                content = await fb.generate(
                    messages=messages,
                    temperature=temperature,
                    timeout=fb_timeout,
                )
                return {
                    "content": content,
                    "provider": fallback_name,
                    "model": getattr(fb, "default_model", "default"),
                    "fallback_used": True,
                }
            except Exception as fb_err:
                raise LLMServiceError(
                    provider=f"{primary_name}->{fallback_name}",
                    reason=f"Primary error: {e} | Fallback error: {fb_err}",
                )

    async def health_check(self) -> Dict[str, Any]:
        """Runs health checks on configured providers."""
        primary_name = settings.LLM_PROVIDER.lower()
        provider = self.get_provider(primary_name)
        status_info = await provider.health_check()
        status_info["fallback_enabled"] = settings.LLM_FALLBACK_ENABLED
        status_info["fallback_provider"] = self._get_fallback_provider_name(primary_name)
        return status_info


# ==============================================================================
# Module-level Factory & Function
# ==============================================================================
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Singleton getter for LLMService."""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance


async def generate_response(
    query: str,
    context: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    timeout: Optional[float] = None,
    enable_fallback: Optional[bool] = None,
) -> str:
    """
    Direct function interface:
    generate_response(query, context)
    """
    service = get_llm_service()
    return await service.generate_response(
        query=query,
        context=context,
        provider=provider,
        model=model,
        temperature=temperature,
        timeout=timeout,
        enable_fallback=enable_fallback,
    )
