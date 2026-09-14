import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
from services.agent_router import AgentRouter, get_agent_router
from models.schemas import AgentRouterRequest, AgentRouterResponse, AnswerData, EssayData, ArtifactData


def test_intent_classification_rules():
    router = AgentRouter()

    # Question -> answer
    intent1, _ = router.classify_intent("How do I measure product-market fit?")
    assert intent1 == "answer"

    intent2, _ = router.classify_intent("What did Brian Chesky say about Founder Mode?")
    assert intent2 == "answer"

    # "write article" -> essay
    intent3, _ = router.classify_intent("write article on 0 to 1 customer acquisition loops")
    assert intent3 == "essay"

    intent4, _ = router.classify_intent("Please write an essay about B2B onboarding friction")
    assert intent4 == "essay"

    intent5, _ = router.classify_intent("Draft a deep-dive newsletter on pricing metrics")
    assert intent5 == "essay"

    # "create page" -> artifact
    intent6, _ = router.classify_intent("create page for a PMF survey tool")
    assert intent6 == "artifact"

    intent7, _ = router.classify_intent("Build landing page for Lenny Growth Assistant")
    assert intent7 == "artifact"

    intent8, _ = router.classify_intent("generate page: retention cohort dashboard")
    assert intent8 == "artifact"


@pytest.mark.asyncio
async def test_router_executes_question_intent():
    router = AgentRouter()
    router.llm_service.generate_response = AsyncMock(
        return_value="Product-Market Fit is confirmed by flattening retention curves."
    )

    req = AgentRouterRequest(prompt="How do I verify PMF?")
    result = await router.route_and_execute(req)

    assert isinstance(result, AgentRouterResponse)
    assert result.type == "answer"
    assert isinstance(result.data, AnswerData)
    assert "PMF" in result.data.query
    assert "retention curves" in result.data.content


@pytest.mark.asyncio
async def test_router_executes_essay_intent():
    router = AgentRouter()
    mock_essay_md = (
        "# The Growth Loops Playbook\n"
        "## Why funnels are dead and loops compound\n\n"
        "**Executive Brief:** Growth loops drive compounding user acquisition.\n\n"
        "### 1. The Core Problem\nFunnels decay linearly.\n\n"
        "### 2. Takeaways\n- Focus on one primary loop\n- Measure loop cycle time"
    )
    router.llm_service.generate_response = AsyncMock(return_value=mock_essay_md)

    req = AgentRouterRequest(prompt="write article on the four growth loops")
    result = await router.route_and_execute(req)

    assert result.type == "essay"
    assert isinstance(result.data, EssayData)
    assert "Growth Loops" in result.data.title
    assert result.data.estimated_read_time_mins >= 1
    assert len(result.data.content) > 50


@pytest.mark.asyncio
async def test_router_executes_artifact_intent():
    router = AgentRouter()
    mock_html = (
        "<!DOCTYPE html>\n"
        "<html lang='en'><head><title>PMF Calculator</title></head>\n"
        "<body class='bg-slate-100'><div class='container'><h1>PMF Score</h1></div></body></html>"
    )
    router.llm_service.generate_response = AsyncMock(return_value=f"```html\n{mock_html}\n```")

    req = AgentRouterRequest(prompt="create page for a Sean Ellis PMF survey calculator")
    result = await router.route_and_execute(req)

    assert result.type == "artifact"
    assert isinstance(result.data, ArtifactData)
    assert "PMF" in result.data.title or "Calculator" in result.data.title
    assert "<!DOCTYPE html>" in result.data.code
    assert result.data.artifact_type == "landing_page"


@pytest.mark.asyncio
async def test_router_api_endpoint(client: AsyncClient):
    payload = {
        "prompt": "write article on early-stage retention heuristics",
    }
    response = await client.post("/router", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert "type" in body
    assert body["type"] == "essay"
    assert "data" in body
    assert "title" in body["data"]
    assert "content" in body["data"]
