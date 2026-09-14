import json
import logging
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and environment settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General Application
    PROJECT_NAME: str = "Lenny Growth Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return list(v)

    # Relational Database (PostgreSQL / Supabase compatible)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_growth"

    # Database Connection Pooling Configuration (Optimized for Supabase / PostgreSQL)
    DB_POOL_SIZE: int = 15
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes recycle to prevent dropped idle sockets
    DB_POOL_PRE_PING: bool = True
    DB_STATEMENT_CACHE_SIZE: int = 0  # Set to 0 when using Supabase/PgBouncer transaction pooler (port 6543)

    # Database Transient Retry Policy
    DB_MAX_RETRIES: int = 3
    DB_RETRY_BASE_DELAY: float = 0.5
    DB_RETRY_MAX_DELAY: float = 3.0

    # Vector Database (Chroma)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "lenny_growth_knowledge"
    CHROMA_PERSISTENCE_DIR: str = "./chroma_data"
    CHROMA_USE_HTTP: bool = True
    RAG_MIN_RELEVANCE_SCORE: float = 0.05

    # LLM Providers (Active: "openai" or "ollama")
    LLM_PROVIDER: str = "openai"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_FALLBACK_ENABLED: bool = True
    LLM_FALLBACK_PROVIDER: str = "ollama"

    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Ollama Settings (Local fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0

    # Session Management
    MAX_SESSION_HISTORY: int = 20
    SESSION_TTL_HOURS: int = 72


settings = Settings()

# Setup logger configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger("backend")
