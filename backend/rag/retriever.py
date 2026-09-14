import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass
class SourceReference:
    """Structured citation reference for a retrieved knowledge chunk."""
    title: str
    source_file: str
    speaker: Optional[str]
    host: str
    chunk_index: int
    relevance_score: float
    excerpt: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    """Encapsulates the retrieved context string and structured source references."""
    query: str
    retrieved_context: str
    source_references: List[SourceReference]
    chunks_retrieved: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "chunks_retrieved": self.chunks_retrieved,
            "source_references": [s.to_dict() for s in self.source_references],
            "retrieved_context": self.retrieved_context,
        }


class LennyTranscriptRetriever:
    """
    RAG Retriever for querying Chroma DB transcript knowledge.
    Retrieves the top-k (default 5) most relevant chunks and formats:
    1. Retrieved Context (for LLM prompt injection)
    2. Source References (for transparent UI citations)
    """

    def __init__(
        self,
        collection_name: str = "lenny_growth_knowledge",
        persist_dir: str = "./chroma_data",
        chroma_host: Optional[str] = "localhost",
        chroma_port: int = 8001,
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port

        self.client = self._init_client()
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def _init_client(self):
        """Initializes Chroma client with HTTP fallback to local PersistentClient."""
        if self.chroma_host:
            try:
                client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                client.heartbeat()
                return client
            except Exception:
                pass

        os.makedirs(self.persist_dir, exist_ok=True)
        return chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> RetrievalResult:
        """
        Retrieves top-k relevant chunks for a user query.
        Returns both formatted context and granular source references.
        """
        clean_query = query.strip()
        if not clean_query:
            return RetrievalResult(
                query=query,
                retrieved_context="No query provided.",
                source_references=[],
                chunks_retrieved=0,
            )

        collection_count = self.collection.count()
        if collection_count == 0:
            return RetrievalResult(
                query=clean_query,
                retrieved_context="Knowledge base is currently empty. Please run ingestion first.",
                source_references=[],
                chunks_retrieved=0,
            )

        n_results = min(top_k, collection_count)

        query_kwargs: Dict[str, Any] = {
            "query_texts": [clean_query],
            "n_results": n_results,
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        references: List[SourceReference] = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0] if results.get("distances") else []

            for idx, doc in enumerate(docs):
                meta = metadatas[idx] if idx < len(metadatas) else {}
                dist = distances[idx] if idx < len(distances) else None

                # Convert L2/cosine distance to similarity score (0.0 to 1.0)
                if dist is not None:
                    score = round(max(0.0, min(1.0, 1.0 - (dist / 2.0))), 4)
                else:
                    score = 1.0

                if score < min_score:
                    continue

                title = meta.get("episode_title") or meta.get("title", "Lenny's Growth Knowledge")
                source_file = meta.get("source_file") or meta.get("source", "podcast_transcript")
                speaker = meta.get("guest") or meta.get("speakers")
                host = meta.get("host", "Lenny Rachitsky")
                chunk_index = meta.get("chunk_index", idx)

                references.append(
                    SourceReference(
                        title=title,
                        source_file=source_file,
                        speaker=speaker,
                        host=host,
                        chunk_index=chunk_index,
                        relevance_score=score,
                        excerpt=doc.strip(),
                        metadata=meta,
                    )
                )

        # Format cohesive context block for LLM prompt
        retrieved_context = self._format_context(references)

        return RetrievalResult(
            query=clean_query,
            retrieved_context=retrieved_context,
            source_references=references,
            chunks_retrieved=len(references),
        )

    def _format_context(self, references: List[SourceReference]) -> str:
        """Formats source references into structured context for LLM injection."""
        if not references:
            return "No relevant context found in knowledge base."

        context_blocks = []
        for i, ref in enumerate(references, 1):
            speaker_tag = f" | Speaker: {ref.speaker}" if ref.speaker else ""
            header = f"[SOURCE {i}] Episode: {ref.title}{speaker_tag} (File: {ref.source_file}, Relevance: {ref.relevance_score})"
            context_blocks.append(f"{header}\n{ref.excerpt}")

        return "\n\n" + ("=" * 70) + "\n" + "\n\n".join(context_blocks) + "\n" + ("=" * 70)


# Singleton factory helper
_retriever_instance: Optional[LennyTranscriptRetriever] = None


def get_retriever(collection_name: str = "lenny_growth_knowledge") -> LennyTranscriptRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = LennyTranscriptRetriever(collection_name=collection_name)
    return _retriever_instance


if __name__ == "__main__":
    import sys
    query_text = sys.argv[1] if len(sys.argv) > 1 else "How do I know if I have Product-Market Fit?"

    retriever = LennyTranscriptRetriever()
    result = retriever.retrieve(query=query_text, top_k=5)

    print(f"\n🔍 Query: '{result.query}'")
    print(f"📦 Retrieved Chunks: {result.chunks_retrieved}")
    print("\n" + "=" * 30 + " RETRIEVED CONTEXT " + "=" * 30)
    print(result.retrieved_context)

    print("\n" + "=" * 30 + " SOURCE REFERENCES " + "=" * 30)
    for i, src in enumerate(result.source_references, 1):
        print(f"\n[{i}] {src.title} (Score: {src.relevance_score})")
        print(f"    Speaker: {src.speaker} | Source: {src.source_file} (Chunk #{src.chunk_index})")
        print(f"    Excerpt: {src.excerpt[:140]}...")
