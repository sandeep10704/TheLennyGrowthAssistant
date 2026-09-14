from typing import Any, Optional, Dict


class AppException(Exception):
    """Base exception for application-level errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_SERVER_ERROR",
        detail: Optional[Any] = None,
        user_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.detail = detail or message
        self.user_message = user_message or message


class SessionNotFoundError(AppException):
    """Raised when a requested session_id is not found."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' was not found.",
            status_code=404,
            code="SESSION_NOT_FOUND",
            detail={"session_id": session_id},
            user_message=f"The conversation session '{session_id}' could not be located. A new session has been initiated.",
        )


class InvalidProviderError(AppException):
    """Raised when an unsupported LLM provider is requested."""
    def __init__(self, provider: str):
        super().__init__(
            message=f"Unsupported LLM provider: '{provider}'. Supported providers are: 'openai', 'ollama'.",
            status_code=400,
            code="INVALID_PROVIDER",
            detail={"provider": provider, "supported": ["openai", "ollama"]},
            user_message=f"'{provider}' is not supported. Please choose 'openai' or 'ollama'.",
        )


class LLMServiceError(AppException):
    """Raised when an external LLM invocation fails."""
    def __init__(self, provider: str, reason: str, user_message: Optional[str] = None):
        clean_user_message = user_message or (
            f"The AI service ({provider.upper()}) encountered an error. Please try again or switch provider."
        )
        super().__init__(
            message=f"LLM generation failed for provider '{provider}': {reason}",
            status_code=502,
            code="LLM_SERVICE_ERROR",
            detail={"provider": provider, "reason": reason},
            user_message=clean_user_message,
        )


class LLMTimeoutError(LLMServiceError):
    """Raised when an LLM provider request exceeds the configured timeout."""
    def __init__(self, provider: str, timeout_seconds: float):
        user_msg = (
            f"The {provider.upper()} model took longer than {timeout_seconds:.0f}s to reply. "
            "The model may be loading or under high load. Please try again with a shorter prompt or switch to a lighter model."
        )
        super().__init__(
            provider=provider,
            reason=f"Request timed out after {timeout_seconds:.0f}s.",
            user_message=user_msg,
        )
        self.code = "LLM_TIMEOUT"
        self.status_code = 504
        self.detail = {
            "provider": provider,
            "timeout_seconds": timeout_seconds,
            "actionable_tip": "Retry query, use a shorter prompt, or select a faster model (e.g. gpt-4o-mini or llama3.1:8b).",
        }


class MissingAPIKeyError(AppException):
    """Raised when an active LLM provider requires an API key that is not configured."""
    def __init__(self, provider: str = "openai", key_name: str = "OPENAI_API_KEY"):
        user_msg = (
            f"The {provider.upper()} API key is missing or unconfigured. "
            f"Add your {key_name} to your .env file, or toggle to the local 'Ollama' provider."
        )
        super().__init__(
            message=f"{key_name} is missing or contains placeholder credentials.",
            status_code=401,
            code="MISSING_API_KEY",
            detail={
                "provider": provider,
                "missing_key": key_name,
                "actionable_tip": f"Add {key_name}=sk-... in .env or switch active provider to 'ollama' in the UI.",
            },
            user_message=user_msg,
        )


class DatabaseError(AppException):
    """Raised when persistent database operations encounter an unrecoverable failure."""
    def __init__(self, operation: str, reason: str):
        user_msg = (
            "Our database service is temporarily unavailable. "
            "Your conversation is currently saved in local memory, but persistent storage is offline."
        )
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            status_code=503,
            code="DATABASE_ERROR",
            detail={
                "operation": operation,
                "reason": reason,
                "actionable_tip": "Check database connectivity or verify PostgreSQL credentials in .env.",
            },
            user_message=user_msg,
        )


class EmptyRAGResultsError(AppException):
    """Raised when semantic retrieval returns 0 documents for queries where knowledge base context is required."""
    def __init__(self, query: str):
        user_msg = (
            f"No direct matches found in Lenny's growth knowledge base for '{query}'. "
            "Try phrasing your query around core concepts like 'retention curves', 'North Star metric', 'PMF benchmarks', or 'pricing'."
        )
        super().__init__(
            message=f"Empty RAG search results for query: '{query}'",
            status_code=404,
            code="EMPTY_RAG_RESULTS",
            detail={
                "query": query,
                "suggestion": "Search for topics covered in Lenny's podcasts, e.g. Growth Loops, PMF, Retention, Pricing.",
            },
            user_message=user_msg,
        )


class VectorStoreError(AppException):
    """Raised when Chroma vector store operations encounter a failure."""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Vector store operation failed: {reason}",
            status_code=502,
            code="VECTOR_STORE_ERROR",
            detail={"reason": reason},
            user_message="Knowledge retrieval service is temporarily unavailable. Answering using general growth frameworks.",
        )
