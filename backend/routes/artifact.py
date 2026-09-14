from fastapi import APIRouter, Depends, status
from models.schemas import ArtifactRequest, ArtifactResponse
from services.artifact_generator import ArtifactGenerator, get_artifact_generator

router = APIRouter(tags=["Artifact Generator"])


@router.post(
    "/artifacts/generate",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate digital artifact (Markdown or HTML/CSS)",
    description=(
        "Generates structured digital artifacts in two primary formats:\n"
        "- `html`: Standalone, interactive HTML5/CSS page with Tailwind CSS CDN and vanilla JS components\n"
        "- `markdown`: Structured technical specification, PRD, or execution checklist\n\n"
        "Returns structured JSON in exact format:\n"
        "```json\n"
        "{\n"
        '  "type": "html" | "markdown",\n'
        '  "content": "..."\n'
        "}\n"
        "```"
    ),
)
async def generate_artifact_endpoint(
    request: ArtifactRequest,
    generator: ArtifactGenerator = Depends(get_artifact_generator),
) -> ArtifactResponse:
    """
    Generate a digital artifact based on the provided prompt and context.
    - If `output_type` is omitted, automatically detects format from prompt keywords.
    - If `html`, returns self-contained HTML5 with Tailwind CSS and interactive JS.
    - If `markdown`, returns GitHub Flavored Markdown with tables, alerts, and task lists.
    """
    return await generator.generate_artifact(
        prompt=request.prompt,
        output_type=request.output_type,
        context=request.context,
        provider=request.provider,
        model=request.model,
    )


@router.post(
    "/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def generate_artifact_alias(
    request: ArtifactRequest,
    generator: ArtifactGenerator = Depends(get_artifact_generator),
) -> ArtifactResponse:
    """Convenience alias for /artifacts/generate."""
    return await generator.generate_artifact(
        prompt=request.prompt,
        output_type=request.output_type,
        context=request.context,
        provider=request.provider,
        model=request.model,
    )
