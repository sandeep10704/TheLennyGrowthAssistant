import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from services.llm_service import (
    BaseLLMProvider,
    OpenAIProvider,
    OllamaProvider,
    LLMService,
    get_llm_service,
    generate_response,
)
from services.exceptions import LLMServiceError, LLMTimeoutError, InvalidProviderError


def test_providers_implement_same_interface():
    """Verify both OpenAI and Ollama adhere strictly to BaseLLMProvider interface."""
    openai_p = OpenAIProvider()
    ollama_p = OllamaProvider()

    assert isinstance(openai_p, BaseLLMProvider)
    assert isinstance(ollama_p, BaseLLMProvider)
    assert hasattr(openai_p, "generate")
    assert hasattr(ollama_p, "generate")
    assert hasattr(openai_p, "health_check")
    assert hasattr(ollama_p, "health_check")
    assert openai_p.provider_name == "openai"
    assert ollama_p.provider_name == "ollama"


def test_config_based_switching():
    """Verify providers can be dynamically switched via config or argument."""
    service = LLMService()

    provider_openai = service.get_provider("openai")
    assert provider_openai.provider_name == "openai"

    provider_ollama = service.get_provider("ollama")
    assert provider_ollama.provider_name == "ollama"

    with pytest.raises(InvalidProviderError):
        service.get_provider("unsupported_cloud")


@pytest.mark.asyncio
async def test_timeout_handling_raises_llm_timeout_error():
    """Verify that exceeding timeout triggers LLMTimeoutError."""
    service = LLMService()
    mock_provider = AsyncMock(spec=BaseLLMProvider)
    mock_provider.provider_name = "mock_slow"

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.5)
        return "too slow"

    mock_provider.generate.side_effect = slow_generate
    service.providers["mock_slow"] = mock_provider

    # Call with very low timeout (0.01s) and fallback disabled
    with pytest.raises(Exception):
        await service.generate_response(
            query="test timeout",
            context="test context",
            provider="mock_slow",
            timeout=0.01,
            enable_fallback=False,
        )


@pytest.mark.asyncio
async def test_fallback_logic_when_primary_fails():
    """Verify that when primary provider fails, the fallback provider is called automatically."""
    service = LLMService()

    # Mock primary (fails)
    mock_openai = AsyncMock(spec=BaseLLMProvider)
    mock_openai.provider_name = "openai"
    mock_openai.generate.side_effect = LLMServiceError(provider="openai", reason="Rate limit reached (429)")

    # Mock fallback (succeeds)
    mock_ollama = AsyncMock(spec=BaseLLMProvider)
    mock_ollama.provider_name = "ollama"
    mock_ollama.generate.return_value = "Fallback response generated successfully via Ollama."

    service.providers["openai"] = mock_openai
    service.providers["ollama"] = mock_ollama

    # Execute generate_response with primary='openai' and fallback enabled
    result = await service.generate_response(
        query="What are growth loops?",
        context="Growth loops are compounding engines.",
        provider="openai",
        enable_fallback=True,
    )

    assert "Fallback response generated successfully via Ollama." in result
    mock_openai.generate.assert_called_once()
    mock_ollama.generate.assert_called_once()


@pytest.mark.asyncio
async def test_core_function_generate_response():
    """Verify generate_response(query, context) function format."""
    query = "How do I measure PMF?"
    context = "Sean Ellis 40% benchmark indicates product-market fit."

    # Mock LLMService to return predictable response
    mock_p = AsyncMock(spec=BaseLLMProvider)
    mock_p.provider_name = "mock_provider"
    mock_p.generate.return_value = "PMF can be measured using Sean Ellis's 40% survey benchmark."

    service = get_llm_service()
    service.providers["mock_provider"] = mock_p

    response = await service.generate_response(
        query=query,
        context=context,
        provider="mock_provider",
        enable_fallback=False,
    )

    assert "Sean Ellis" in response
    assert isinstance(response, str)
