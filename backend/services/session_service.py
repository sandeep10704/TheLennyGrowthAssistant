import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from config.settings import settings, logger
from models.database import async_session_factory, ChatSessionModel, ChatMessageModel
from models.schemas import SourceCitation, SessionDetailResponse, ChatMessageItem
from services.exceptions import SessionNotFoundError


class SessionService:
    """
    Manages session-based conversational state and message persistence.
    Uses PostgreSQL as primary persistence with in-memory LRU caching.
    """

    def __init__(self):
        # In-memory fallback/cache: session_id -> list of message dicts
        self._memory_cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self._cache_limit = 500

    def _cache_put(self, session_id: str, message: Dict[str, Any]):
        if session_id not in self._memory_cache:
            if len(self._memory_cache) >= self._cache_limit:
                self._memory_cache.popitem(last=False)
            self._memory_cache[session_id] = []
        self._memory_cache[session_id].append(message)
        self._memory_cache.move_to_end(session_id)

    async def get_or_create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Verify existing session or create a new one."""
        sid = session_id or str(uuid.uuid4())

        # If it was already in memory cache, we're good
        if sid in self._memory_cache and session_id:
            return sid

        try:
            async with async_session_factory() as db:
                result = await db.execute(select(ChatSessionModel).where(ChatSessionModel.id == sid))
                existing = result.scalar_one_or_none()

                if not existing:
                    new_session = ChatSessionModel(
                        id=sid,
                        title=title or "Growth Advisory Session",
                    )
                    db.add(new_session)
                    await db.commit()
                return sid
        except Exception as e:
            logger.debug(f"DB session query fallback to memory: {e}")
            if sid not in self._memory_cache:
                self._memory_cache[sid] = []
            return sid

    async def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for LLM context injection."""
        # 1. Check database first
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatMessageModel)
                    .where(ChatMessageModel.session_id == session_id)
                    .order_by(desc(ChatMessageModel.created_at))
                    .limit(limit)
                )
                messages = list(reversed(result.scalars().all()))
                if messages:
                    return [{"role": m.role, "content": m.content} for m in messages]
        except Exception as e:
            logger.debug(f"DB history lookup error ({e}), falling back to memory cache.")

        # 2. Memory cache fallback
        if session_id in self._memory_cache:
            recent = self._memory_cache[session_id][-limit:]
            return [{"role": m["role"], "content": m["content"]} for m in recent]

        return []

    async def add_user_message(self, session_id: str, content: str) -> str:
        """Append user message to session."""
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Store in cache
        self._cache_put(
            session_id,
            {
                "id": msg_id,
                "role": "user",
                "content": content,
                "created_at": now,
            },
        )

        # Store in database
        try:
            async with async_session_factory() as db:
                msg = ChatMessageModel(
                    id=msg_id,
                    session_id=session_id,
                    role="user",
                    content=content,
                    created_at=now,
                )
                db.add(msg)
                await db.commit()
        except Exception as e:
            logger.debug(f"DB insert user message notice: {e}")

        return msg_id

    async def add_assistant_message(
        self,
        session_id: str,
        content: str,
        sources: List[SourceCitation],
        model_used: str,
    ) -> str:
        """Append assistant response to session."""
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        sources_payload = [s.model_dump() for s in sources]

        # Store in cache
        self._cache_put(
            session_id,
            {
                "id": msg_id,
                "role": "assistant",
                "content": content,
                "sources": sources_payload,
                "model_used": model_used,
                "created_at": now,
            },
        )

        # Store in database
        try:
            async with async_session_factory() as db:
                msg = ChatMessageModel(
                    id=msg_id,
                    session_id=session_id,
                    role="assistant",
                    content=content,
                    sources=sources_payload,
                    model_used=model_used,
                    created_at=now,
                )
                db.add(msg)
                await db.commit()
        except Exception as e:
            logger.debug(f"DB insert assistant message notice: {e}")

        return msg_id

    async def get_session_details(self, session_id: str) -> SessionDetailResponse:
        """Get complete session information with all message history."""
        # Try database first
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel)
                    .where(ChatSessionModel.id == session_id)
                    .options(selectinload(ChatSessionModel.messages))
                )
                session = result.scalar_one_or_none()
                if session:
                    items = [
                        ChatMessageItem(
                            id=m.id,
                            role=m.role,
                            content=m.content,
                            sources=m.sources,
                            model_used=m.model_used,
                            created_at=m.created_at,
                        )
                        for m in session.messages
                    ]
                    return SessionDetailResponse(
                        session_id=session.id,
                        message_count=len(items),
                        messages=items,
                        created_at=session.created_at,
                        updated_at=session.updated_at,
                    )
        except Exception as e:
            logger.debug(f"DB session fetch notice: {e}")

        # Try memory cache
        if session_id in self._memory_cache:
            cached_msgs = self._memory_cache[session_id]
            now = datetime.now(timezone.utc)
            items = [
                ChatMessageItem(
                    id=m.get("id", str(uuid.uuid4())),
                    role=m["role"],
                    content=m["content"],
                    sources=m.get("sources"),
                    model_used=m.get("model_used"),
                    created_at=m.get("created_at", now),
                )
                for m in cached_msgs
            ]
            return SessionDetailResponse(
                session_id=session_id,
                message_count=len(items),
                messages=items,
                created_at=now,
                updated_at=now,
            )

        raise SessionNotFoundError(session_id=session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Remove a session from memory and database."""
        deleted = False
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
            deleted = True

        try:
            async with async_session_factory() as db:
                result = await db.execute(select(ChatSessionModel).where(ChatSessionModel.id == session_id))
                sess = result.scalar_one_or_none()
                if sess:
                    await db.delete(sess)
                    await db.commit()
                    deleted = True
        except Exception as e:
            logger.debug(f"DB delete notice: {e}")

        return deleted


_session_service_instance: Optional[SessionService] = None


def get_session_service() -> SessionService:
    global _session_service_instance
    if _session_service_instance is None:
        _session_service_instance = SessionService()
    return _session_service_instance
