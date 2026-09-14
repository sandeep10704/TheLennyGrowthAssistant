import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from services.exceptions import (
    DatabaseError,
    LLMTimeoutError,
    MissingAPIKeyError,
    EmptyRAGResultsError,
    LLMServiceError,
)
from services.llm_service import OpenAIProvider, OllamaProvider, LLMService
from services.session_service import SessionService
from services.vector_service import VectorService
from services.chat_service import ChatService
from models.schemas import ChatRequest, ErrorResponse


# ==============================================================================
# 1. DB Failure Tests
# ==============================================================================
def test_database_error_schema_and_user_friendly_message():
    """Verify DatabaseError provides clear user-friendly explanation and actionable tip."""
    exc = DatabaseError(operation="Store Message", reason="Connection refused on port 5432")
    assert exc.status_code == 503
    assert exc.code == "DATABASE_ERROR"
    assert "database service is temporarily unavailable" in exc.user_message.lower()
    assert "actionable_tip" in exc.detail
    assert "PostgreSQL" in exc.detail["actionable_tip"] or "connectivity" in exc.detail["actionable_tip"]


@pytest.mark.asyncio
async def test_session_service_memory_fallback_on_db_failure():
    """Verify that when PostgreSQL is unreachable, SessionService falls back to memory cache seamlessly."""
    session_service = SessionService()
    test_sid = "test-fallback-session-999"

    # Simulate database failure during session auto-create
    with patch("services.session_service.execute_with_db_retry", side_effect=Exception("Database down")):
        sid = await session_service.get_or_create_session(session_id=test_sid, title="Fallback Session")
        assert sid == test_sid
        assert test_sid in session_service._memory_cache

        # Store user message into in-memory store
        msg_id = await session_service.add_user_message(session_id=test_sid, content="Hello from offline DB mode")
        assert msg_id is not None

        # Verify message is preserved in memory cache
        history = await session_service.get_session_history(session_id=test_sid)
        assert len(history) == 1
        assert history[0]["content"] == "Hello from offline DB mode"


# ==============================================================================
# 2. LLM Timeout Tests
# ==============================================================================
def test_llm_timeout_error_schema_and_user_friendly_message():
    """Verify LLMTimeoutError produces HTTP 504 and helpful load/timeout advice."""
    exc = LLMTimeoutError(provider="openai", timeout_seconds=30.0)
    assert exc.status_code == 504
    assert exc.code == "LLM_TIMEOUT"
    assert "longer than 30s" in exc.user_message
    assert "detail" in dir(exc)
    assert exc.detail["timeout_seconds"] == 30.0
    assert "actionable_tip" in exc.detail


@pytest.mark.asyncio
async def test_llm_service_timeout_handling():
    """Verify provider timeout triggers LLMTimeoutError with actionable tip."""
    service = LLMService()
    slow_provider = AsyncMock()
    slow_provider.provider_name = "mock_timeout"

    async def sleep_and_timeout(*args, **kwargs):
        await asyncio.sleep(0.5)
        return "response"

    slow_provider.generate.side_effect = sleep_and_timeout
    service.providers["mock_timeout"] = slow_provider

    with pytest.raises(Exception):
        await service.generate_response(
            query="Testing timeout",
            context="None",
            provider="mock_timeout",
            timeout=0.01,
            enable_fallback=False,
        )


# ==============================================================================
# 3. Empty RAG Results Tests
# ==============================================================================
def test_empty_rag_results_error_schema():
    """Verify EmptyRAGResultsError produces HTTP 404 with guidance on search concepts."""
    exc = EmptyRAGResultsError(query="unrelated non-product topic")
    assert exc.status_code == 404
    assert exc.code == "EMPTY_RAG_RESULTS"
    assert "No direct matches found" in exc.user_message
    assert "retention curves" in exc.user_message or "PMF benchmarks" in exc.user_message
    assert "suggestion" in exc.detail


@pytest.mark.asyncio
async def test_chat_service_require_rag_flag_raises_empty_rag_error():
    """Verify that when require_rag=True and 0 chunks match, EmptyRAGResultsError is raised."""
    mock_vector = MagicMock(spec=VectorService)
    mock_vector.query_knowledge.return_value = []  # 0 chunks found

    chat_service = ChatService(vector_service=mock_vector)

    req = ChatRequest(
        message="xyzrandomquerythatyieldszerochunks",
        require_rag=True,
    )

    with pytest.raises(EmptyRAGResultsError):
        await chat_service.process_chat(req)


@pytest.mark.asyncio
async def test_chat_service_normal_query_with_empty_rag_uses_graceful_fallback():
    """Verify that normal chat does NOT crash on empty RAG, but injects baseline heuristics."""
    mock_vector = MagicMock(spec=VectorService)
    mock_vector.query_knowledge.return_value = []  # 0 chunks

    mock_llm = AsyncMock(spec=LLMService)
    mock_llm.generate_chat_turn.return_value = {
        "content": "Here is advice based on Lenny's core growth frameworks.",
        "provider": "openai",
        "model": "gpt-4o-mini",
    }

    mock_session = AsyncMock(spec=SessionService)
    mock_session.get_or_create_session.return_value = "session-123"
    mock_session.add_user_message.return_value = "msg-user-1"
    mock_session.get_session_history.return_value = []
    mock_session.add_assistant_message.return_value = "msg-asst-1"

    chat_service = ChatService(
        session_service=mock_session,
        vector_service=mock_vector,
        llm_service=mock_llm,
    )

    req = ChatRequest(
        message="General strategic question without direct citations",
        require_rag=False,
    )

    response = await chat_service.process_chat(req)
    assert response is not None
    assert response.sources == []
    assert "Lenny's core growth frameworks" in response.content


# ==============================================================================
# 4. Missing API Keys Tests
# ==============================================================================
def test_missing_api_key_error_schema():
    """Verify MissingAPIKeyError produces HTTP 401 with .env and Ollama instructions."""
    exc = MissingAPIKeyError(provider="openai", key_name="OPENAI_API_KEY")
    assert exc.status_code == 401
    assert exc.code == "MISSING_API_KEY"
    assert "OPENAI API key is missing" in exc.user_message
    assert "toggle to the local 'Ollama'" in exc.user_message
    assert exc.detail["missing_key"] == "OPENAI_API_KEY"
    assert "actionable_tip" in exc.detail


@pytest.mark.asyncio
async def test_openai_provider_raises_missing_api_key_when_unconfigured():
    """Verify OpenAIProvider raises MissingAPIKeyError when API key is empty or placeholder."""
    provider = OpenAIProvider()
    provider.api_key = ""
    provider.client = None

    with pytest.raises(MissingAPIKeyError) as exc_info:
        await provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert exc_info.value.code == "MISSING_API_KEY"
    assert exc_info.value.status_code == 401

    # Also test placeholder pattern
    provider.api_key = "your_openai_api_key_here"
    with pytest.raises(MissingAPIKeyError):
        await provider.generate(messages=[{"role": "user", "content": "hello"}])


# ==============================================================================
# 5. Global FastAPI Exception Handlers Integration Tests
# ==============================================================================
def test_fastapi_app_exception_handler_returns_standard_error_response():
    """Verify FastAPI routes format domain AppException into user-friendly ErrorResponse JSON."""
    client = TestClient(app)

    # Trigger EmptyRAGResultsError via /knowledge/search
    response = client.get("/knowledge/search?query=qwertyuiopnonexistentconcept12345")
    assert response.status_code == 404

    data = response.json()
    assert data["success"] is False
    assert data["code"] == "EMPTY_RAG_RESULTS"
    assert "user_message" in data
    assert "actionable_tip" in data
    assert data["actionable_tip"] is not None
    assert "No direct matches found" in data["user_message"]
