import pytest
import os
from rag.ingestion import TranscriptIngestionPipeline, count_tokens
from rag.retriever import LennyTranscriptRetriever, RetrievalResult, SourceReference


def test_token_counter():
    text = "Product-Market Fit is not a binary milestone; it is a gradient and phase change."
    tokens = count_tokens(text)
    assert tokens > 0
    assert tokens < 50


def test_transcript_loading_and_metadata_parsing():
    pipeline = TranscriptIngestionPipeline(
        collection_name="test_temp_collection",
        persist_dir="./test_chroma_data",
    )
    docs = pipeline.load_transcripts("data/transcripts")
    assert len(docs) >= 3

    # Check parsed metadata
    titles = [d["title"] for d in docs]
    assert any("Brian Chesky" in t for t in titles)
    assert any("Sean Ellis" in t for t in titles)
    assert any("Shreyas Doshi" in t for t in titles)


def test_chunking_token_boundaries():
    pipeline = TranscriptIngestionPipeline(
        collection_name="test_temp_collection",
        persist_dir="./test_chroma_data",
        min_chunk_tokens=50,
        max_chunk_tokens=800,
        overlap_tokens=30,
    )
    docs = pipeline.load_transcripts("data/transcripts/sean_ellis_pmf_and_growth.txt")
    assert len(docs) == 1

    chunks = pipeline.chunk_transcript(docs[0])
    assert len(chunks) >= 1

    for chunk in chunks:
        assert chunk.token_count > 0
        assert chunk.episode_title is not None
        assert chunk.chunk_id.startswith(docs[0]["doc_id"])
        meta = chunk.to_metadata()
        assert "episode_title" in meta
        assert "token_count" in meta
        assert "source_file" in meta


def test_retriever_context_and_sources_formatting():
    retriever = LennyTranscriptRetriever(
        collection_name="test_temp_collection",
        persist_dir="./test_chroma_data",
    )
    # Even if empty or populated, it must return a valid RetrievalResult object
    result = retriever.retrieve("How do I measure PMF?", top_k=5)
    assert isinstance(result, RetrievalResult)
    assert hasattr(result, "retrieved_context")
    assert hasattr(result, "source_references")
    assert isinstance(result.source_references, list)
    assert result.chunks_retrieved <= 5
