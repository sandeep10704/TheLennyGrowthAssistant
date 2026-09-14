from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.api.deps import get_db_session, get_vector_service
from app.services.vector_store import VectorStoreService
from app.services.llm.factory import get_llm_service
from app.schemas.health import HealthResponse, ComponentStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def check_health(
    db: AsyncSession = Depends(get_db_session),
    vector_store: VectorStoreService = Depends(get_vector_service),
):
    """
    Comprehensive health check verifying connectivity to:
    - PostgreSQL database (Supabase compatible)
    - Chroma vector database
    - Configured LLM provider (OpenAI or Ollama)
    """
    # 1. Check PostgreSQL
    db_status = ComponentStatus(status="healthy", details={"url": settings.DATABASE_URL.split("@")[-1]})
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = ComponentStatus(
            status="degraded",
            details={"error": f"Database unreachable: {str(e)}"},
        )

    # 2. Check Vector DB (Chroma)
    chroma_health = vector_store.health_check()
    vector_status = ComponentStatus(
        status=chroma_health.get("status", "unknown"),
        details=chroma_health,
    )

    # 3. Check LLM Service
    llm = get_llm_service()
    llm_health = await llm.health_check()
    llm_status = ComponentStatus(
        status=llm_health.get("status", "unknown"),
        details=llm_health,
    )

    overall_healthy = (
        db_status.status == "healthy"
        and vector_status.status == "healthy"
        and llm_status.status == "ready"
    )

    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        database=db_status,
        vector_store=vector_status,
        llm=llm_status,
    )
