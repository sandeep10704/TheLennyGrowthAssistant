from typing import List
from fastapi import APIRouter, Depends, status
from app.api.deps import get_vector_service
from app.services.vector_store import VectorStoreService
from app.schemas.document import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
)

router = APIRouter()


@router.post("/documents/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED, tags=["Knowledge Base"])
async def ingest_documents(
    payload: DocumentIngestRequest,
    vector_store: VectorStoreService = Depends(get_vector_service),
):
    """
    Ingest text documents or playbook chunks into the Chroma vector database.
    Documents are automatically indexed for RAG retrieval during chat queries.
    """
    count = vector_store.add_documents(payload.documents)
    return DocumentIngestResponse(
        status="success",
        chunks_indexed=count,
        message=f"Successfully indexed {count} document chunks into vector database.",
    )


@router.post("/documents/search", response_model=List[DocumentSearchResult], tags=["Knowledge Base"])
async def search_documents(
    payload: DocumentSearchRequest,
    vector_store: VectorStoreService = Depends(get_vector_service),
):
    """
    Direct semantic vector similarity search against the knowledge base.
    """
    results = vector_store.query_similar(query_text=payload.query, n_results=payload.n_results)
    return [
        DocumentSearchResult(
            id=r.get("metadata", {}).get("id", "doc_chunk"),
            content=r["content"],
            metadata=r.get("metadata", {}),
            distance=r.get("relevance_score"),
        )
        for r in results
    ]


@router.get("/documents/stats", tags=["Knowledge Base"])
async def get_vector_stats(
    vector_store: VectorStoreService = Depends(get_vector_service),
):
    """Retrieve vector database collection statistics."""
    return vector_store.health_check()
