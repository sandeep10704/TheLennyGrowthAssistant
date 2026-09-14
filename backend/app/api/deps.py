from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.vector_store import VectorStoreService, get_vector_store
from app.services.assistant import LennyGrowthAssistant, get_assistant


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_vector_service() -> VectorStoreService:
    return get_vector_store()


def get_assistant_service() -> LennyGrowthAssistant:
    return get_assistant()
