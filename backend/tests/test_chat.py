import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_creates_new_session(client: AsyncClient):
    payload = {
        "message": "How do I know if our company has reached Product-Market Fit?",
    }
    response = await client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0
    assert "content" in data
    assert "sources" in data
    assert data["role"] == "assistant"
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_chat_maintains_session_history(client: AsyncClient):
    # Turn 1
    res1 = await client.post("/chat", json={"message": "What is a North Star Metric?"})
    assert res1.status_code == 200
    session_id = res1.json()["session_id"]

    # Turn 2 using the same session_id
    res2 = await client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Can you give me an example for Airbnb?",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["session_id"] == session_id

    # Turn 3: Fetch full session history
    hist_res = await client.get(f"/chat/sessions/{session_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["session_id"] == session_id
    assert hist_data["message_count"] >= 4  # 2 user msgs + 2 assistant msgs


@pytest.mark.asyncio
async def test_validation_error_handling(client: AsyncClient):
    # Empty message should trigger 422 with structured ErrorResponse
    response = await client.post("/chat", json={"message": ""})
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["code"] == "VALIDATION_ERROR"
    assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_provider_error_handling(client: AsyncClient):
    # Unsupported provider should trigger 400 InvalidProviderError
    response = await client.post(
        "/chat",
        json={"message": "Hello", "provider": "unsupported_llm"},
    )
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["code"] == "INVALID_PROVIDER"
