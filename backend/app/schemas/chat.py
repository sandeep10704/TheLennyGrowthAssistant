from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    title: Optional[str] = "Knowledge Base Document"
    source: Optional[str] = None
    content: str
    relevance_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageCreate(BaseModel):
    role: str = Field(..., description="Message author role: user, assistant, or system")
    content: str = Field(..., description="Content of the message")
    sources: Optional[List[SourceCitation]] = None
    model_used: Optional[str] = None


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Growth Chat"


class ConversationRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationRead):
    messages: List[MessageRead] = []


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or prompt for Lenny Growth Assistant")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID to resume")
    provider: Optional[str] = Field(None, description="Override LLM provider: 'openai' or 'ollama'")
    model: Optional[str] = Field(None, description="Override model name (e.g., gpt-4o, llama3)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    top_k_sources: Optional[int] = Field(4, ge=1, le=10, description="Number of knowledge chunks to retrieve")


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    sources: List[SourceCitation] = []
    provider: str
    model: str
    created_at: datetime
