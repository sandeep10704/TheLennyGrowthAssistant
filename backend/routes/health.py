from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import text

from config.settings import settings, logger
from models.schemas import HealthResponse, HealthComponentStatus
from models.database import async_session_factory, get_connection_pool_stats
from services.vector_service import get_vector_service
from services.llm_service import get_llm_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
async def health_check():
    """
    Comprehensive health check for:
    - Relational Database (PostgreSQL / Supabase) with Connection Pool stats
    - Vector Database (Chroma)
    - Active LLM Provider (OpenAI / Ollama)
    """
    # 1. Database & Pool Check
    pool_stats = get_connection_pool_stats()
    db_status = HealthComponentStatus(
        status="healthy",
        details={"type": "postgresql/supabase", "pool": pool_stats},
    )
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = HealthComponentStatus(
            status="degraded",
            details={"error": f"Database unreachable: {str(e)}", "pool": pool_stats},
        )

    # 2. Vector DB Check
    vector_service = get_vector_service()
    chroma_meta = vector_service.health_check()
    vector_status = HealthComponentStatus(
        status=chroma_meta.get("status", "unknown"),
        details=chroma_meta,
    )

    # 3. LLM Provider Check
    llm_service = get_llm_service()
    llm_meta = await llm_service.health_check()
    llm_status = HealthComponentStatus(
        status=llm_meta.get("status", "unknown"),
        details=llm_meta,
    )

    is_overall_healthy = (
        db_status.status == "healthy"
        and vector_status.status == "healthy"
        and llm_status.status == "ready"
    )

    return HealthResponse(
        status="healthy" if is_overall_healthy else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        components={
            "database": db_status,
            "vector_store": vector_status,
            "llm": llm_status,
        },
    )
