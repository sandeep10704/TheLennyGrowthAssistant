import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
from services.artifact_generator import (
    ArtifactGenerator,
    get_artifact_generator,
    generate_artifact,
)
from models.schemas import ArtifactRequest, ArtifactResponse


# ==============================================================================
# Format Detection Tests
# ==============================================================================
def test_detect_format_heuristics():
    generator = ArtifactGenerator()

    # 1. HTML / CSS / UI intent
    assert generator.detect_format("create page for onboarding flow") == "html"
    assert generator.detect_format("build a landing page for PMF survey") == "html"
    assert generator.detect_format("generate an interactive calculator for LTV:CAC") == "html"
    assert generator.detect_format("design dashboard for retention cohorts") == "html"
    assert generator.detect_format("create a web form for customer feedback") == "html"

    # 2. Markdown / Docs / PRD intent
    assert generator.detect_format("create checklist for product launch") == "markdown"
    assert generator.detect_format("generate PRD for self-serve onboarding") == "markdown"
    assert generator.detect_format("write markdown documentation for growth loops") == "markdown"
    assert generator.detect_format("spec for churn diagnostic framework") == "markdown"
    assert generator.detect_format("create a cheatsheet of B2B retention benchmarks") == "markdown"

    # 3. Explicit type override precedence
    assert generator.detect_format("create page", explicit_type="markdown") == "markdown"
    assert generator.detect_format("write spec", explicit_type="html") == "html"


# ==============================================================================
# HTML Artifact Generation Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_generate_html_artifact_mocked_llm():
    generator = ArtifactGenerator()
    mock_html = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <title>Growth Loop Simulator</title>\n"
        "  <script src=\"https://cdn.tailwindcss.com\"></script>\n"
        "</head>\n"
        "<body class=\"bg-slate-50 p-8\">\n"
        "  <h1 class=\"text-2xl font-bold\">Viral Coefficient Calculator</h1>\n"
        "  <div id=\"result\">K-factor: 1.2</div>\n"
        "  <script>console.log('simulator loaded');</script>\n"
        "</body>\n"
        "</html>"
    )
    generator.llm_service.generate_response = AsyncMock(
        return_value=f"```html\n{mock_html}\n```"
    )

    response = await generator.generate_artifact(
        prompt="create page for viral coefficient simulator",
        output_type="html",
    )

    assert isinstance(response, ArtifactResponse)
    assert response.type == "html"
    assert "<!DOCTYPE html>" in response.content
    assert "cdn.tailwindcss.com" in response.content
    assert "Growth Loop Simulator" in response.content
    assert "<script>" in response.content

    # Verify dictionary serialization matches user spec exactly:
    # { "type": "html" | "markdown", "content": "..." }
    dump = response.model_dump()
    assert set(dump.keys()) == {"type", "content"}
    assert dump["type"] == "html"


@pytest.mark.asyncio
async def test_generate_html_artifact_fallback():
    generator = ArtifactGenerator()
    # Simulate LLM failure / offline state
    generator.llm_service.generate_response = AsyncMock(
        side_effect=Exception("LLM inference service unavailable")
    )

    response = await generator.generate_artifact(
        prompt="create page for Sean Ellis PMF survey",
        output_type="html",
    )

    assert isinstance(response, ArtifactResponse)
    assert response.type == "html"
    assert "<!DOCTYPE html>" in response.content
    assert "cdn.tailwindcss.com" in response.content
    assert "Sean Ellis PMF" in response.content
    assert "updateScore" in response.content  # Interactive JS embedded


# ==============================================================================
# Markdown Artifact Generation Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_generate_markdown_artifact_mocked_llm():
    generator = ArtifactGenerator()
    mock_md = (
        "# Product Launch Readiness Specification\n\n"
        "> [!IMPORTANT]\n"
        "> Verify all items before code freeze.\n\n"
        "## Benchmarks\n"
        "| Metric | Target | Status |\n"
        "| :--- | :--- | :--- |\n"
        "| PMF Score | >= 40% | Pass |\n\n"
        "## Checklist\n"
        "- [x] Fix critical bug\n"
        "- [ ] Configure PostHog tracking\n"
    )
    generator.llm_service.generate_response = AsyncMock(
        return_value=f"```markdown\n{mock_md}\n```"
    )

    response = await generator.generate_artifact(
        prompt="create spec for product launch readiness",
        output_type="markdown",
    )

    assert isinstance(response, ArtifactResponse)
    assert response.type == "markdown"
    assert response.content.startswith("# Product Launch Readiness Specification")
    assert "| Metric | Target | Status |" in response.content
    assert "- [x]" in response.content
    assert "> [!IMPORTANT]" in response.content

    # Strict JSON structure check
    dump = response.model_dump()
    assert set(dump.keys()) == {"type", "content"}
    assert dump["type"] == "markdown"


@pytest.mark.asyncio
async def test_generate_markdown_artifact_fallback():
    generator = ArtifactGenerator()
    generator.llm_service.generate_response = AsyncMock(
        side_effect=Exception("LLM network timeout")
    )

    response = await generator.generate_artifact(
        prompt="create checklist for product launch",
        output_type="markdown",
    )

    assert isinstance(response, ArtifactResponse)
    assert response.type == "markdown"
    assert response.content.startswith("# ")
    assert "| Metric | Healthy Threshold |" in response.content
    assert "- [x]" in response.content
    assert "- [ ]" in response.content
    assert "> [!NOTE]" in response.content


# ==============================================================================
# Module Level Function & API Route Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_generate_artifact_module_function():
    response = await generate_artifact(
        prompt="create page for Sean Ellis survey calculator",
        output_type="html",
    )
    assert isinstance(response, ArtifactResponse)
    assert response.type == "html"
    assert len(response.content) > 50


@pytest.mark.asyncio
async def test_artifact_api_endpoint(client: AsyncClient):
    # Test POST /artifacts/generate
    payload = {
        "prompt": "build landing page for retention cohort analyzer",
        "output_type": "html",
    }
    res = await client.post("/artifacts/generate", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert "type" in data
    assert "content" in data
    assert data["type"] == "html"
    assert "<!DOCTYPE html>" in data["content"]
    assert "cdn.tailwindcss.com" in data["content"]


@pytest.mark.asyncio
async def test_artifact_api_endpoint_markdown(client: AsyncClient):
    # Test auto-detection via prompt
    payload = {
        "prompt": "create checklist for pre-launch growth experiments",
    }
    res = await client.post("/artifacts/generate", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["type"] == "markdown"
    assert "# " in data["content"]
    assert "- [" in data["content"]
