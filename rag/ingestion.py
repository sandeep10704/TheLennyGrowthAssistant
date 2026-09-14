import os
import re
import glob
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import chromadb
from chromadb.config import Settings as ChromaSettings

# ------------------------------------------------------------------------------
# Token Counting Utility (tiktoken with fallback)
# ------------------------------------------------------------------------------
try:
    import tiktoken
    _TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_TIKTOKEN_ENCODER.encode(text))

except ImportError:
    def count_tokens(text: str) -> int:
        # Standard token heuristic: ~1.33 tokens per word
        words = text.split()
        return max(1, int(len(words) * 1.33))


@dataclass
class TranscriptChunk:
    """Represents an ingested text chunk with rich provenance metadata."""
    chunk_id: str
    doc_id: str
    content: str
    token_count: int
    episode_title: str
    guest: Optional[str]
    host: Optional[str]
    source_file: str
    chunk_index: int
    total_chunks: int = 0
    speakers: Optional[List[str]] = None

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "episode_title": self.episode_title,
            "guest": self.guest or "Unknown",
            "host": self.host or "Lenny Rachitsky",
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "token_count": self.token_count,
            "speakers": ", ".join(self.speakers) if self.speakers else "Unknown",
        }


class TranscriptIngestionPipeline:
    """
    RAG Ingestion Pipeline:
    1. Loads transcript files (.txt, .md, .json)
    2. Parses speaker turns and episode metadata
    3. Chunks text into 500–800 token windows with semantic boundary preservation
    4. Generates embeddings
    5. Stores / upserts into Chroma Vector DB
    """

    def __init__(
        self,
        collection_name: str = "lenny_growth_knowledge",
        persist_dir: str = "./chroma_data",
        chroma_host: Optional[str] = "localhost",
        chroma_port: int = 8001,
        min_chunk_tokens: int = 500,
        max_chunk_tokens: int = 800,
        overlap_tokens: int = 60,
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

        self.chroma_client = self._init_chroma()
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )

    def _init_chroma(self):
        """Initializes Chroma client with HTTP server or local PersistentClient fallback."""
        if self.chroma_host:
            try:
                client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                client.heartbeat()
                print(f"Connected to ChromaDB HTTP at {self.chroma_host}:{self.chroma_port}")
                return client
            except Exception:
                pass

        os.makedirs(self.persist_dir, exist_ok=True)
        print(f"Using local Chroma PersistentClient at {self.persist_dir}")
        return chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    # --------------------------------------------------------------------------
    # Step 1: Load Transcript Files
    # --------------------------------------------------------------------------
    def load_transcripts(self, path: str) -> List[Dict[str, Any]]:
        """
        Loads transcripts from a single file or a directory.
        Supports .txt, .md, and .json formats.
        """
        target_path = Path(path)
        raw_documents = []

        if target_path.is_file():
            files = [target_path]
        elif target_path.is_dir():
            files = list(target_path.glob("*.txt")) + list(target_path.glob("*.md")) + list(target_path.glob("*.json"))
        else:
            # Try glob pattern
            files = [Path(p) for p in glob.glob(path)]

        if not files:
            print(f"Warning: No transcript files found at '{path}'.")
            return []

        for f in files:
            try:
                if f.suffix.lower() == ".json":
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        content = data.get("transcript", "") or data.get("content", "") or json.dumps(data)
                        title = data.get("episode_title", f.stem.replace("_", " ").title())
                        guest = data.get("guest")
                        host = data.get("host", "Lenny Rachitsky")
                else:
                    with open(f, "r", encoding="utf-8") as fp:
                        content = fp.read()
                    title, guest, host, content = self._extract_header_metadata(f.name, content)

                doc_id = hashlib.sha256(f.name.encode()).hexdigest()[:12]
                raw_documents.append({
                    "doc_id": doc_id,
                    "filename": f.name,
                    "filepath": str(f.resolve()),
                    "title": title,
                    "guest": guest,
                    "host": host,
                    "content": content.strip(),
                })
            except Exception as e:
                print(f"Error reading transcript '{f}': {e}")

        print(f"Successfully loaded {len(raw_documents)} transcript file(s).")
        return raw_documents

    def _extract_header_metadata(self, filename: str, content: str) -> Tuple[str, Optional[str], Optional[str], str]:
        """Extracts title, guest, and host metadata from text headers."""
        title = Path(filename).stem.replace("_", " ").title()
        guest = None
        host = "Lenny Rachitsky"

        lines = content.splitlines()
        body_start_idx = 0

        for i, line in enumerate(lines[:15]):
            line_str = line.strip()
            if line_str.lower().startswith("episode title:"):
                title = line_str.split(":", 1)[1].strip()
                body_start_idx = max(body_start_idx, i + 1)
            elif line_str.lower().startswith("guest:"):
                guest = line_str.split(":", 1)[1].strip()
                body_start_idx = max(body_start_idx, i + 1)
            elif line_str.lower().startswith("host:"):
                host = line_str.split(":", 1)[1].strip()
                body_start_idx = max(body_start_idx, i + 1)
            elif line_str.startswith("[00:"):
                body_start_idx = min(body_start_idx, i) if body_start_idx > 0 else i
                break

        body_content = "\n".join(lines[body_start_idx:]).strip()
        return title, guest, host, body_content or content

    # --------------------------------------------------------------------------
    # Step 2: Chunk Text (500–800 tokens)
    # --------------------------------------------------------------------------
    def chunk_transcript(self, document: Dict[str, Any]) -> List[TranscriptChunk]:
        """
        Chunks transcript text into 500-800 token windows.
        Respects dialogue turns and paragraph boundaries with sliding overlap.
        """
        content = document["content"]
        doc_id = document["doc_id"]
        title = document["title"]
        guest = document["guest"]
        host = document["host"]
        filename = document["filename"]

        # Split into semantic segments (speaker turns or double newlines)
        # Matches patterns like "[00:01:23] Speaker Name:" or "\n\n"
        raw_segments = re.split(r"(?=\[\d{2}:\d{2}:\d{2}\]|\n\n+)", content)
        segments = [s.strip() for s in raw_segments if s.strip()]

        chunks: List[TranscriptChunk] = []
        current_segments: List[str] = []
        current_tokens = 0
        chunk_idx = 0

        for seg in segments:
            seg_tokens = count_tokens(seg)

            # If a single segment exceeds max_chunk_tokens, break by sentences
            if seg_tokens > self.max_chunk_tokens:
                sub_sentences = re.split(r"(?<=[.!?])\s+", seg)
                for sent in sub_sentences:
                    sent_tokens = count_tokens(sent)
                    if current_tokens + sent_tokens > self.max_chunk_tokens and current_tokens >= self.min_chunk_tokens:
                        # Finalize chunk
                        chunk_text = " ".join(current_segments).strip()
                        chunks.append(
                            self._build_chunk(
                                doc_id=doc_id,
                                chunk_idx=chunk_idx,
                                content=chunk_text,
                                title=title,
                                guest=guest,
                                host=host,
                                filename=filename,
                            )
                        )
                        chunk_idx += 1
                        # Retain overlap
                        overlap_tail = self._get_overlap_tail(current_segments, self.overlap_tokens)
                        current_segments = overlap_tail + [sent]
                        current_tokens = sum(count_tokens(s) for s in current_segments)
                    else:
                        current_segments.append(sent)
                        current_tokens += sent_tokens
                continue

            # Standard segment accumulation
            if current_tokens + seg_tokens > self.max_chunk_tokens and current_tokens >= self.min_chunk_tokens:
                chunk_text = "\n\n".join(current_segments).strip()
                chunks.append(
                    self._build_chunk(
                        doc_id=doc_id,
                        chunk_idx=chunk_idx,
                        content=chunk_text,
                        title=title,
                        guest=guest,
                        host=host,
                        filename=filename,
                    )
                )
                chunk_idx += 1
                overlap_tail = self._get_overlap_tail(current_segments, self.overlap_tokens)
                current_segments = overlap_tail + [seg]
                current_tokens = sum(count_tokens(s) for s in current_segments)
            else:
                current_segments.append(seg)
                current_tokens += seg_tokens

        # Final dangling chunk
        if current_segments:
            chunk_text = "\n\n".join(current_segments).strip()
            if count_tokens(chunk_text) >= 50:  # Ignore trivial endings
                chunks.append(
                    self._build_chunk(
                        doc_id=doc_id,
                        chunk_idx=chunk_idx,
                        content=chunk_text,
                        title=title,
                        guest=guest,
                        host=host,
                        filename=filename,
                    )
                )

        # Update total_chunks metadata
        total = len(chunks)
        for c in chunks:
            c.total_chunks = total

        return chunks

    def _get_overlap_tail(self, segments: List[str], target_overlap_tokens: int) -> List[str]:
        """Extracts the final segments approximating target_overlap_tokens."""
        tail = []
        tokens = 0
        for seg in reversed(segments):
            seg_tokens = count_tokens(seg)
            if tokens + seg_tokens <= target_overlap_tokens or not tail:
                tail.insert(0, seg)
                tokens += seg_tokens
            else:
                break
        return tail

    def _build_chunk(
        self,
        doc_id: str,
        chunk_idx: int,
        content: str,
        title: str,
        guest: Optional[str],
        host: Optional[str],
        filename: str,
    ) -> TranscriptChunk:
        chunk_id = f"{doc_id}_chunk_{chunk_idx:04d}"
        tokens = count_tokens(content)

        # Extract speakers present in this specific chunk
        speaker_matches = re.findall(r"(?:\[\d{2}:\d{2}:\d{2}\]\s+)?([A-Z][a-zA-Z\s]{1,30}):", content)
        speakers = list(dict.fromkeys(speaker_matches)) if speaker_matches else []

        return TranscriptChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            content=content,
            token_count=tokens,
            episode_title=title,
            guest=guest,
            host=host,
            source_file=filename,
            chunk_index=chunk_idx,
            speakers=speakers,
        )

    # --------------------------------------------------------------------------
    # Step 3 & 4: Embed & Store in Chroma DB
    # --------------------------------------------------------------------------
    def store_chunks(self, chunks: List[TranscriptChunk], batch_size: int = 64) -> int:
        """
        Embeds and stores chunks into Chroma DB.
        Uses upsert to make ingestion idempotent and prevent duplicate entries.
        """
        if not chunks:
            return 0

        total_stored = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [c.chunk_id for c in batch]
            documents = [c.content for c in batch]
            metadatas = [c.to_metadata() for c in batch]

            # Upsert into Chroma (automatically embeds using Chroma's embedding pipeline)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            total_stored += len(batch)

        print(f"Stored {total_stored} chunks in Chroma collection '{self.collection_name}'.")
        return total_stored

    # --------------------------------------------------------------------------
    # Full Pipeline Execution
    # --------------------------------------------------------------------------
    def run(self, source_path: str = "data/transcripts") -> Dict[str, Any]:
        """Runs the complete ingestion pipeline: Load -> Chunk -> Store."""
        print(f"\n🚀 Starting RAG Ingestion Pipeline from '{source_path}'...")
        documents = self.load_transcripts(source_path)

        all_chunks: List[TranscriptChunk] = []
        for doc in documents:
            chunks = self.chunk_transcript(doc)
            print(f" - {doc['filename']}: {len(chunks)} chunks created (avg {sum(c.token_count for c in chunks)//max(1, len(chunks))} tokens/chunk)")
            all_chunks.extend(chunks)

        total_stored = self.store_chunks(all_chunks)
        collection_count = self.collection.count()

        summary = {
            "files_processed": len(documents),
            "chunks_created": len(all_chunks),
            "chunks_stored": total_stored,
            "total_collection_chunks": collection_count,
            "collection_name": self.collection_name,
        }
        print(f"✅ Ingestion complete! Total items in collection: {collection_count}\n")
        return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest transcripts into Chroma DB")
    parser.add_argument("--path", default="data/transcripts", help="Path to transcript file or directory")
    parser.add_argument("--collection", default="lenny_growth_knowledge", help="Chroma collection name")
    args = parser.parse_args()

    pipeline = TranscriptIngestionPipeline(collection_name=args.collection)
    pipeline.run(source_path=args.path)
