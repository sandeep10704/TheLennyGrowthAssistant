import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.core.logging import logger
from app.schemas.document import DocumentChunk


DEFAULT_GROWTH_PLAYBOOK = [
    {
        "title": "Finding Product-Market Fit (PMF)",
        "source": "Lenny's Newsletter: The PMF Guide",
        "content": (
            "Product-Market Fit (PMF) is not a single point in time, but a phase change. "
            "Key signals of PMF: (1) A retention curve that flattens parallel to the x-axis over time. "
            "(2) The Sean Ellis benchmark: >40% of survey respondents state they would be 'very disappointed' "
            "if your product ceased to exist. (3) Exponential organic word-of-mouth pull where demand outpaces supply. "
            "Until retention flattens, do not spend money scaling acquisition."
        ),
    },
    {
        "title": "The 4 Growth Loops That Drive Modern Startups",
        "source": "Lenny's Podcast: Growth Frameworks",
        "content": (
            "Sustainable growth comes from compounding loops, not linear top-of-funnel acquisition. "
            "The four foundational growth loops are: (1) Viral Loop: A user uses the product and directly exposes others (e.g., Figma, Zoom, Slack). "
            "(2) Content/SEO Loop: Users or companies generate indexable content that attracts new users via search (e.g., Pinterest, TripAdvisor, StackOverflow). "
            "(3) Paid Marketing Loop: High LTV generates cash flow to reinvest into ads with <12 month payback. "
            "(4) Sales Loop: High-ACV enterprise contracts fund outbound sales teams. Choose one primary loop to master first."
        ),
    },
    {
        "title": "Defining Your North Star Metric",
        "source": "Lenny's Guide to North Star Metrics",
        "content": (
            "A North Star Metric (NSM) is the single metric that best captures the core value your product provides to customers. "
            "It aligns product, marketing, and engineering around value creation rather than vanity vanity metrics. "
            "Examples: Airbnb uses 'Nights Booked', Spotify uses 'Time Spent Listening', Miro uses 'Collaborative Boards Created'. "
            "Your NSM should be a leading indicator of revenue, not revenue itself."
        ),
    },
    {
        "title": "Tactics for Acquiring Your First 1,000 Users",
        "source": "Lenny's Research: How Top Startups Got Started",
        "content": (
            "The first 1,000 users require doing things that don't scale (Paul Graham). "
            "The seven most common paths: (1) Going directly to offline communities (e.g., DoorDash handing out flyers at Stanford). "
            "(2) Tapping online communities like Reddit, Hacker News, or specialized Slack channels. "
            "(3) Leveraging high-friction FOMO and exclusive invite lists (e.g., Superhuman, Clubhouse). "
            "(4) Finding influencers and industry champions to co-sign. "
            "(5) Creating lightweight utility tools or calculators that provide instant value."
        ),
    },
    {
        "title": "Retention is the Foundation of All Growth",
        "source": "Lenny's Growth Principles",
        "content": (
            "If your product has poor retention, pouring more users into the top of the funnel is like pouring water into a leaky bucket. "
            "To fix retention: (1) Measure cohort retention by days/weeks. (2) Identify your 'Aha! moment'—the action that correlates with long-term retention "
            "(e.g., Facebook's '7 friends in 10 days', Slack's '2,000 team messages sent'). (3) Remove all friction leading up to that moment."
        ),
    },
    {
        "title": "Pricing, Packaging, and Willingness to Pay",
        "source": "Lenny's Guide to Monetization",
        "content": (
            "Most startups price their products too low. Your pricing should be tied to your 'Value Metric'—the unit by which customers derive value "
            "(e.g., per seat, per active contact, per gigabyte, per transaction). "
            "Use the Van Westendorp Price Sensitivity Meter to test four price perceptions: too cheap, bargain, expensive, and prohibitively expensive."
        ),
    },
]


class VectorStoreService:
    def __init__(self):
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.client = self._init_client()
        self.collection = self._get_or_create_collection()
        self.seed_default_knowledge()

    def _init_client(self):
        """Initializes Chroma client with automatic fallback to persistent client."""
        if settings.CHROMA_USE_HTTP:
            try:
                client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                client.heartbeat()
                logger.info(f"Connected to ChromaDB HTTP server at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
                return client
            except Exception as e:
                logger.warning(
                    f"ChromaDB HTTP connection failed ({e}). Falling back to local PersistentClient."
                )

        # Fallback to local directory
        os.makedirs(settings.CHROMA_PERSISTENCE_DIR, exist_ok=True)
        return chromadb.PersistentClient(
            path=settings.CHROMA_PERSISTENCE_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _get_or_create_collection(self):
        try:
            return self.client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.error(f"Error accessing collection {self.collection_name}: {e}")
            raise

    def seed_default_knowledge(self) -> None:
        """Seeds initial growth knowledge items if the collection is empty."""
        try:
            count = self.collection.count()
            if count == 0:
                logger.info("Seeding Chroma vector database with Lenny's Growth Playbook...")
                ids = [f"seed_{i+1}" for i in range(len(DEFAULT_GROWTH_PLAYBOOK))]
                documents = [item["content"] for item in DEFAULT_GROWTH_PLAYBOOK]
                metadatas = [
                    {"title": item["title"], "source": item["source"]}
                    for item in DEFAULT_GROWTH_PLAYBOOK
                ]
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                logger.info(f"Successfully seeded {len(ids)} growth playbook items.")
        except Exception as e:
            logger.warning(f"Could not seed default knowledge into Chroma: {e}")

    def add_documents(self, documents: List[DocumentChunk]) -> int:
        """Add custom documents or chunks to the vector database."""
        ids = [doc.id or str(uuid.uuid4()) for doc in documents]
        texts = [doc.content for doc in documents]
        metadatas = [
            {
                "title": doc.title or "Knowledge Item",
                "source": doc.source or "manual_upload",
                **(doc.metadata or {}),
            }
            for doc in documents
        ]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )
        return len(ids)

    def query_similar(self, query_text: str, n_results: int = 4) -> List[Dict[str, Any]]:
        """Query nearest matching chunks by semantic similarity."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, max(1, self.collection.count())),
            )

            chunks = []
            if results and results.get("documents") and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0] if results.get("distances") else []

                for idx, doc in enumerate(docs):
                    meta = metadatas[idx] if idx < len(metadatas) else {}
                    dist = distances[idx] if idx < len(distances) else None
                    chunks.append({
                        "content": doc,
                        "title": meta.get("title", "Growth Resource"),
                        "source": meta.get("source", "Knowledge Base"),
                        "metadata": meta,
                        "relevance_score": round(1.0 - dist, 4) if dist is not None else None,
                    })
            return chunks
        except Exception as e:
            logger.error(f"Vector search query failed: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {
                "status": "healthy",
                "collection": self.collection_name,
                "document_count": count,
            }
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
            }


_vector_store_instance: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance
