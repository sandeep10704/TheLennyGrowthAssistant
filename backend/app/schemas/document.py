from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    id: Optional[str] = None
    content: str = Field(..., min_length=1, description="Text chunk content")
    title: Optional[str] = "Growth Knowledge Item"
    source: Optional[str] = "internal_playbook"
    metadata: Optional[Dict[str, Any]] = None


class DocumentIngestRequest(BaseModel):
    documents: List[DocumentChunk]


class DocumentIngestResponse(BaseModel):
    status: str = "success"
    chunks_indexed: int
    message: str


class DocumentSearchRequest(BaseModel):
    query: str
    n_results: int = Field(5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    distance: Optional[float] = None
