from typing import Any, Optional


class AppException(Exception):
    """Base exception for application-level errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_SERVER_ERROR",
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.detail = detail or message


class SessionNotFoundError(AppException):
    """Raised when a requested session_id is not found."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' was not found.",
            status_code=404,
            code="SESSION_NOT_FOUND",
            detail={"session_id": session_id},
        )


class InvalidProviderError(AppException):
    """Raised when an unsupported LLM provider is requested."""
    def __init__(self, provider: str):
        super().__init__(
            message=f"Unsupported LLM provider: '{provider}'. Supported providers are: 'openai', 'ollama'.",
            status_code=400,
            code="INVALID_PROVIDER",
            detail={"provider": provider, "supported": ["openai", "ollama"]},
        )


class LLMServiceError(AppException):
    """Raised when an external LLM invocation fails."""
    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"LLM generation failed for provider '{provider}': {reason}",
            status_code=502,
            code="LLM_SERVICE_ERROR",
            detail={"provider": provider, "reason": reason},
        )


class VectorStoreError(AppException):
    """Raised when Chroma vector store operations encounter a failure."""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Vector store operation failed: {reason}",
            status_code=502,
            code="VECTOR_STORE_ERROR",
            detail={"reason": reason},
        )
