from typing import Dict, Any
from pydantic import BaseModel


class ComponentStatus(BaseModel):
    status: str  # "healthy", "degraded", "unavailable"
    details: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded"
    version: str
    environment: str
    database: ComponentStatus
    vector_store: ComponentStatus
    llm: ComponentStatus
