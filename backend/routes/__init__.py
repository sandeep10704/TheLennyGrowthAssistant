from fastapi import APIRouter
from routes.health import router as health_router
from routes.chat import router as chat_router

api_router = APIRouter()

# Mount endpoints
api_router.include_router(health_router)
api_router.include_router(chat_router)

__all__ = ["api_router", "health_router", "chat_router"]
