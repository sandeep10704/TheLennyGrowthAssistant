from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Citation information for knowledge retrieved from vector store."""
    title: str = Field(default="Growth Playbook Knowledge", description="Document title")
    source: Optional[str] = Field(default=None, description="Source publication or author")
    content: str = Field(..., description="Excerpt content used to ground response")
    relevance_score: Optional[float] = Field(default=None, description="Semantic similarity score (0.0 - 1.0)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional document metadata")


class ChatRequest(BaseModel):
    """Request payload for sending a chat message to the growth assistant."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's prompt or growth question",
        examples=["How do I measure whether my product has reached Product-Market Fit?"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session ID to maintain conversation context across turns. If omitted, a new session is generated.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    provider: Optional[str] = Field(
        default=None,
        description="Override LLM provider ('openai' or 'ollama'). Defaults to system configuration.",
        examples=["openai"]
    )
    model: Optional[str] = Field(
        default=None,
        description="Override LLM model name (e.g., 'gpt-4o', 'llama3').",
        examples=["gpt-4o"]
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for creativity vs precision."
    )
    top_k_sources: Optional[int] = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of relevant knowledge chunks to retrieve from vector store (default: 5)."
    )


class ChatResponse(BaseModel):
    """Response payload returned by the assistant."""
    session_id: str = Field(..., description="The session ID associated with this conversation turn")
    message_id: str = Field(..., description="Unique ID of the assistant's message")
    role: str = Field(default="assistant", description="Role of the sender")
    content: str = Field(..., description="Generated growth advice and answer")
    sources: List[SourceCitation] = Field(default_factory=list, description="Grounding citations retrieved from Chroma")
    provider: str = Field(..., description="LLM provider that generated the response")
    model: str = Field(..., description="Model name used")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of generation")


class ChatMessageItem(BaseModel):
    """Individual message item inside session history."""
    id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    """Full session details with message history."""
    session_id: str
    message_count: int
    messages: List[ChatMessageItem]
    created_at: datetime
    updated_at: datetime


class HealthComponentStatus(BaseModel):
    status: str = Field(..., description="'healthy', 'degraded', or 'unreachable'")
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """System health check response schema."""
    status: str = Field(..., description="Overall system health: 'healthy' or 'degraded'")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Active environment name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: Dict[str, HealthComponentStatus] = Field(..., description="Subsystem status checks")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""
    success: bool = False
    error: str = Field(..., description="Brief error classification")
    detail: Optional[Any] = Field(default=None, description="Detailed explanation or validation details")
    code: str = Field(..., description="Machine-readable error code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
