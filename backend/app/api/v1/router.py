from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.documents import router as documents_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="", tags=["Health"])
api_router.include_router(chat_router, prefix="", tags=["Chat & Conversations"])
api_router.include_router(documents_router, prefix="", tags=["Knowledge Base"])
