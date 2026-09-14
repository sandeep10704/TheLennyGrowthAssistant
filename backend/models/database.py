import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, List, Any, Dict
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from config.settings import settings, logger
from services.db_retry import execute_with_db_retry


class Base(DeclarativeBase):
    """Declarative Base for SQLAlchemy ORM models."""
    pass


class ChatSessionModel(Base):
    """Relational table representing a user conversation session."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="Growth Advisory Session", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    messages: Mapped[List["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.created_at",
        lazy="selectin",
    )


class ChatMessageModel(Base):
    """Relational table storing individual messages in a session."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    session: Mapped["ChatSessionModel"] = relationship("ChatSessionModel", back_populates="messages")


def create_pooled_engine() -> AsyncEngine:
    """
    Constructs an asynchronous SQLAlchemy engine equipped with:
    - Connection pooling (pool_size, max_overflow, pool_timeout, pool_recycle)
    - Connection pre-ping to prune dead sockets
    - Statement caching disabled for Supabase / PgBouncer compatibility
    """
    connect_args: Dict[str, Any] = {}

    # Supabase Transaction Pooler (port 6543) or PgBouncer compatibility
    # Disable prepared statement caching in asyncpg to avoid "prepared statement already exists"
    if ":6543" in settings.DATABASE_URL or "pooler.supabase.com" in settings.DATABASE_URL or settings.DB_STATEMENT_CACHE_SIZE == 0:
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0

    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        # Connection Pooling Parameters
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        connect_args=connect_args,
    )


engine: AsyncEngine = create_pooled_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_connection_pool_stats() -> Dict[str, Any]:
    """Inspect and return real-time connection pool metrics."""
    pool = engine.pool
    try:
        return {
            "pool_size": pool.size(),
            "checked_in_connections": pool.checkedin(),
            "checked_out_connections": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "recycle_seconds": settings.DB_POOL_RECYCLE,
            "pre_ping": settings.DB_POOL_PRE_PING,
        }
    except Exception as e:
        return {"error": str(e)}


async def init_db() -> None:
    """Initialize relational database tables on startup using retry logic."""
    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        await execute_with_db_retry(
            _init,
            max_retries=settings.DB_MAX_RETRIES,
            operation_name="Database Schema Init",
        )
        logger.info("Database schemas verified/created successfully (Supabase/PostgreSQL).")
    except Exception as e:
        logger.warning(f"Database initialization warning (PostgreSQL not connected?): {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for SQLAlchemy async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
