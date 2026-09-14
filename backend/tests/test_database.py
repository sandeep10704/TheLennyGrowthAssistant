import pytest
import asyncio
from sqlalchemy.exc import OperationalError
from models.database import get_connection_pool_stats
from services.session_service import get_session_service
from services.db_retry import execute_with_db_retry, with_db_retry
from models.schemas import SourceCitation


@pytest.mark.asyncio
async def test_connection_pool_stats():
    stats = get_connection_pool_stats()
    assert "pool_size" in stats
    assert "checked_in_connections" in stats
    assert "checked_out_connections" in stats
    assert "recycle_seconds" in stats
    assert stats["pre_ping"] is True


@pytest.mark.asyncio
async def test_auto_create_session():
    service = get_session_service()

    # 1. Auto-create when no session_id is provided
    sid1 = await service.get_or_create_session(title="Auto Session 1")
    assert sid1 is not None
    assert len(sid1) > 0

    # 2. Auto-create when custom session_id is provided
    custom_sid = "custom-test-session-12345"
    sid2 = await service.get_or_create_session(session_id=custom_sid, title="Custom Session")
    assert sid2 == custom_sid


@pytest.mark.asyncio
async def test_store_and_retrieve_messages():
    service = get_session_service()
    sid = await service.get_or_create_session()

    # 1. Store User Message
    msg1_id = await service.add_user_message(session_id=sid, content="How do I calculate LTV:CAC?")
    assert msg1_id is not None

    # 2. Store Assistant Message with Sources
    sources = [
        SourceCitation(
            title="LTV:CAC Benchmarks",
            content="A healthy SaaS business targets LTV:CAC > 3:1.",
            relevance_score=0.95,
        )
    ]
    msg2_id = await service.add_assistant_message(
        session_id=sid,
        content="Target an LTV:CAC ratio of at least 3x with <12mo payback period.",
        sources=sources,
        model_used="openai:gpt-4o",
    )
    assert msg2_id is not None

    # 3. Retrieve Session History
    history = await service.get_session_history(session_id=sid, limit=5)
    assert len(history) >= 2
    assert history[-2]["role"] == "user"
    assert "LTV:CAC" in history[-2]["content"]
    assert history[-1]["role"] == "assistant"
    assert "payback" in history[-1]["content"]

    # 4. Retrieve Full Details
    details = await service.get_session_details(session_id=sid)
    assert details.session_id == sid
    assert details.message_count >= 2


@pytest.mark.asyncio
async def test_retry_logic_recovers_from_transient_failures():
    attempts = 0

    async def flaky_db_query():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise OperationalError("SSL connection closed unexpectedly", {}, Exception())
        return "query_success"

    result = await execute_with_db_retry(
        flaky_db_query,
        max_retries=3,
        base_delay=0.01,
        max_delay=0.05,
        operation_name="Test Flaky Query",
    )

    assert result == "query_success"
    assert attempts == 3
