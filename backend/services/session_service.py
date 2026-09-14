import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from config.settings import settings, logger
from models.database import (
    async_session_factory,
    ChatSessionModel,
    ChatMessageModel,
)
from models.schemas import SourceCitation, SessionDetailResponse, ChatMessageItem
from services.exceptions import SessionNotFoundError
from services.db_retry import execute_with_db_retry


class SessionService:
    """
    Production-ready session manager for PostgreSQL (Supabase compatible).
    Features:
    - Auto-create session if not provided or doesn't exist
    - Store user and assistant messages
    - Retrieve session history with ordering
    - Transient DB error retry logic with exponential backoff
    - High-speed in-memory fallback cache
    """

    def __init__(self):
        # In-memory fallback/cache: session_id -> list of message dicts
        self._memory_cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self._sessions_meta_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_limit = 500

    def _cache_put(self, session_id: str, message: Dict[str, Any]):
        if session_id not in self._memory_cache:
            if len(self._memory_cache) >= self._cache_limit:
                self._memory_cache.popitem(last=False)
            self._memory_cache[session_id] = []
        self._memory_cache[session_id].append(message)
        self._memory_cache.move_to_end(session_id)
        if session_id in self._sessions_meta_cache:
            self._sessions_meta_cache[session_id]["updated_at"] = datetime.now(timezone.utc)

    # --------------------------------------------------------------------------
    # 1. Auto-Create Session
    # --------------------------------------------------------------------------
    async def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        Retrieves an existing session or automatically creates a new one in PostgreSQL.
        If session_id is None, generates a new UUID.
        If session_id is given but not in DB, automatically creates the session.
        """
        sid = (session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4()))
        default_title = title or "Growth Advisory Session"

        async def _db_get_or_create():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel).where(ChatSessionModel.id == sid)
                )
                session = result.scalar_one_or_none()

                if not session:
                    # Auto-create session
                    logger.info(f"Auto-creating new session '{sid}' in PostgreSQL...")
                    session = ChatSessionModel(
                        id=sid,
                        title=default_title,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(session)
                    await db.commit()
                return sid

        try:
            return await execute_with_db_retry(
                _db_get_or_create,
                operation_name="Auto-Create Session",
            )
        except Exception as e:
            logger.warning(f"Database auto-create session fallback to memory: {e}")
            if sid not in self._memory_cache:
                self._memory_cache[sid] = []
                self._sessions_meta_cache[sid] = {
                    "id": sid,
                    "title": default_title,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            return sid

    # --------------------------------------------------------------------------
    # 2. Store Messages
    # --------------------------------------------------------------------------
    async def add_user_message(self, session_id: str, content: str) -> str:
        """
        Stores a user message in PostgreSQL and updates session's updated_at timestamp.
        Auto-creates the session if it doesn't already exist.
        """
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Update in-memory cache
        self._cache_put(
            session_id,
            {
                "id": msg_id,
                "role": "user",
                "content": content,
                "sources": None,
                "model_used": None,
                "created_at": now,
            },
        )

        async def _db_store_user():
            async with async_session_factory() as db:
                # Ensure parent session exists (auto-create if missing)
                result = await db.execute(
                    select(ChatSessionModel).where(ChatSessionModel.id == session_id)
                )
                session = result.scalar_one_or_none()
                if not session:
                    session = ChatSessionModel(
                        id=session_id,
                        title=content[:40] + ("..." if len(content) > 40 else ""),
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(session)
                    await db.flush()
                else:
                    session.updated_at = now

                # Insert user message
                msg = ChatMessageModel(
                    id=msg_id,
                    session_id=session_id,
                    role="user",
                    content=content,
                    created_at=now,
                )
                db.add(msg)
                await db.commit()
                return msg_id

        try:
            return await execute_with_db_retry(
                _db_store_user,
                operation_name="Store User Message",
            )
        except Exception as e:
            logger.warning(f"Database store user message notice (using cache): {e}")
            return msg_id

    async def add_assistant_message(
        self,
        session_id: str,
        content: str,
        sources: List[SourceCitation],
        model_used: str,
    ) -> str:
        """
        Stores an assistant message in PostgreSQL with citations and model metadata.
        """
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        sources_payload = [s.model_dump() for s in sources]

        # Update in-memory cache
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

        async def _db_store_assistant():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel).where(ChatSessionModel.id == session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    session.updated_at = now

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
                return msg_id

        try:
            return await execute_with_db_retry(
                _db_store_assistant,
                operation_name="Store Assistant Message",
            )
        except Exception as e:
            logger.warning(f"Database store assistant message notice (using cache): {e}")
            return msg_id

    # --------------------------------------------------------------------------
    # 3. Retrieve Session History
    # --------------------------------------------------------------------------
    async def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieves recent conversation history for a session to inject into LLM prompts.
        Returns messages in chronological order (oldest to newest).
        """
        async def _db_get_history():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatMessageModel)
                    .where(ChatMessageModel.session_id == session_id)
                    .order_by(desc(ChatMessageModel.created_at))
                    .limit(limit)
                )
                # Reverse to get chronological order [oldest ... newest]
                messages = list(reversed(result.scalars().all()))
                return [{"role": m.role, "content": m.content} for m in messages]

        try:
            history = await execute_with_db_retry(
                _db_get_history,
                operation_name="Retrieve Session History",
            )
            if history:
                return history
        except Exception as e:
            logger.debug(f"DB session history lookup error ({e}), falling back to memory cache.")

        # In-memory fallback
        if session_id in self._memory_cache:
            recent = self._memory_cache[session_id][-limit:]
            return [{"role": m["role"], "content": m["content"]} for m in recent]

        return []

    async def get_session_details(self, session_id: str) -> SessionDetailResponse:
        """
        Retrieves full session metadata and complete chronological message history.
        """
        async def _db_get_details():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel)
                    .where(ChatSessionModel.id == session_id)
                    .options(selectinload(ChatSessionModel.messages))
                )
                session = result.scalar_one_or_none()
                if not session:
                    return None

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

        try:
            details = await execute_with_db_retry(
                _db_get_details,
                operation_name="Get Session Details",
            )
            if details:
                return details
        except Exception as e:
            logger.debug(f"DB session details fetch notice ({e}), checking memory cache.")

        # In-memory fallback
        if session_id in self._memory_cache:
            cached_msgs = self._memory_cache[session_id]
            meta = self._sessions_meta_cache.get(session_id, {})
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
                created_at=meta.get("created_at", now),
                updated_at=meta.get("updated_at", now),
            )

        raise SessionNotFoundError(session_id=session_id)

    async def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List active sessions sorted by last activity."""
        async def _db_list():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel)
                    .order_by(desc(ChatSessionModel.updated_at))
                    .limit(limit)
                )
                sessions = result.scalars().all()
                return [
                    {
                        "session_id": s.id,
                        "title": s.title,
                        "created_at": s.created_at.isoformat(),
                        "updated_at": s.updated_at.isoformat(),
                    }
                    for s in sessions
                ]

        try:
            return await execute_with_db_retry(
                _db_list,
                operation_name="List Sessions",
            )
        except Exception as e:
            logger.debug(f"DB list sessions error ({e}), returning cache list.")
            return [
                {
                    "session_id": sid,
                    "title": meta.get("title", "Growth Session"),
                    "created_at": meta.get("created_at", datetime.now(timezone.utc)).isoformat(),
                    "updated_at": meta.get("updated_at", datetime.now(timezone.utc)).isoformat(),
                }
                for sid, meta in self._sessions_meta_cache.items()
            ]

    async def delete_session(self, session_id: str) -> bool:
        """Deletes a session and cascades to delete all messages."""
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
        if session_id in self._sessions_meta_cache:
            del self._sessions_meta_cache[session_id]

        async def _db_delete():
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ChatSessionModel).where(ChatSessionModel.id == session_id)
                )
                sess = result.scalar_one_or_none()
                if sess:
                    await db.delete(sess)
                    await db.commit()
                    return True
                return False

        try:
            return await execute_with_db_retry(
                _db_delete,
                operation_name="Delete Session",
            )
        except Exception as e:
            logger.debug(f"DB delete session error: {e}")
            return False


_session_service_instance: Optional[SessionService] = None


def get_session_service() -> SessionService:
    global _session_service_instance
    if _session_service_instance is None:
        _session_service_instance = SessionService()
    return _session_service_instance
