from fastapi import APIRouter
from routes.health import router as health_router
from routes.chat import router as chat_router
from routes.agent import router as agent_router
from routes.artifact import router as artifact_router

api_router = APIRouter()

# Mount endpoints
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(agent_router)
api_router.include_router(artifact_router)

__all__ = ["api_router", "health_router", "chat_router", "agent_router", "artifact_router"]
