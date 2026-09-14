import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from config.settings import settings, logger
from models.schemas import SourceCitation

DEFAULT_LENNY_KNOWLEDGE = [
    {
        "title": "Finding Product-Market Fit (PMF)",
        "source": "Lenny's Newsletter: The PMF Guide",
        "content": (
            "Product-Market Fit (PMF) is not binary; it is a gradient and phase change. "
            "Key signals of PMF: (1) Flattening cohort retention curves parallel to the x-axis. "
            "(2) Sean Ellis benchmark: >40% of survey respondents state they would be 'very disappointed' "
            "if your product disappeared tomorrow. (3) Exponential organic word-of-mouth pull where "
            "inbound demand outpaces your capacity to serve it. Do not spend aggressively on paid acquisition before PMF."
        ),
    },
    {
        "title": "The 4 Foundation Growth Loops",
        "source": "Lenny's Podcast: Growth Frameworks",
        "content": (
            "Sustainable compounding growth is powered by self-reinforcing loops, not linear funnels. "
            "The 4 loops are: (1) Viral Loop: product usage inherently exposes new prospects (e.g. Figma, Zoom, Calendly). "
            "(2) Content/SEO Loop: users or the platform generate indexable search content (e.g. Pinterest, Tripadvisor, StackOverflow). "
            "(3) Paid Loop: high LTV and cash margins fund customer acquisition with <12-month payback. "
            "(4) Sales Loop: enterprise contract value funds direct outbound sales reps. Master one primary loop before diversifying."
        ),
    },
    {
        "title": "Defining Your North Star Metric",
        "source": "Lenny's Guide to North Star Metrics",
        "content": (
            "A North Star Metric (NSM) captures the core value delivered to your customer. "
            "It aligns product, marketing, and engineering on value creation rather than superficial vanity metrics. "
            "Examples: Airbnb uses 'Nights Booked', Spotify uses 'Time Spent Listening', Miro uses 'Collaborative Boards Active'. "
            "Your North Star Metric must be a leading indicator of revenue, not revenue itself."
        ),
    },
    {
        "title": "Acquiring Your First 1,000 Users",
        "source": "Lenny's Research: How Top Startups Got Started",
        "content": (
            "The earliest 1,000 users are almost always acquired by 'doing things that don't scale'. "
            "Top strategies: (1) In-person grass-roots outreach (DoorDash handing flyers on Stanford campus). "
            "(2) Targeted online communities (Reddit, Hacker News, niche Slack/Discord groups). "
            "(3) Manufactured scarcity & invite-only waitlists (Superhuman, Clubhouse). "
            "(4) Building lightweight single-purpose utility calculators and tools."
        ),
    },
    {
        "title": "Retention is the Foundation of All Growth",
        "source": "Lenny's Growth Principles",
        "content": (
            "Pouring top-of-funnel acquisition into a product with bad retention is pouring water into a leaky bucket. "
            "Steps to fix retention: (1) Measure daily/weekly cohort retention. "
            "(2) Identify the 'Aha! moment' that correlates with long-term retention (e.g. Slack's 2,000 team messages). "
            "(3) Eliminate friction on the activation path to get users to that moment as quickly as possible."
        ),
    },
    {
        "title": "Pricing & Value Metric Alignment",
        "source": "Lenny's Monetization Playbook",
        "content": (
            "Most early-stage companies underprice. Align your pricing structure to your 'Value Metric'—the dimension "
            "along which customers perceive value (per seat, per gigabyte, per tracked transaction). "
            "Use the Van Westendorp Price Sensitivity Meter to identify optimal pricing bands."
        ),
    },
]


class VectorService:
    """Manages Chroma vector store connection and semantic similarity searches."""

    def __init__(self):
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.client = self._init_client()
        self.collection = self._get_or_create_collection()
        self._seed_default_knowledge()

    def _init_client(self):
        if settings.CHROMA_USE_HTTP:
            try:
                client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                client.heartbeat()
                logger.info(f"Connected to ChromaDB HTTP service at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
                return client
            except Exception as e:
                logger.warning(f"ChromaDB HTTP connection failed ({e}). Falling back to local PersistentClient.")

        os.makedirs(settings.CHROMA_PERSISTENCE_DIR, exist_ok=True)
        return chromadb.PersistentClient(
            path=settings.CHROMA_PERSISTENCE_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _get_or_create_collection(self):
        try:
            return self.client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.error(f"Error accessing Chroma collection '{self.collection_name}': {e}")
            raise

    def _seed_default_knowledge(self) -> None:
        try:
            if self.collection.count() == 0:
                logger.info("Vector store is empty. Seeding Lenny Growth knowledge base...")
                ids = [f"lenny_seed_{i+1}" for i in range(len(DEFAULT_LENNY_KNOWLEDGE))]
                docs = [item["content"] for item in DEFAULT_LENNY_KNOWLEDGE]
                metadatas = [
                    {"title": item["title"], "source": item["source"]}
                    for item in DEFAULT_LENNY_KNOWLEDGE
                ]
                self.collection.add(ids=ids, documents=docs, metadatas=metadatas)
                logger.info(f"Successfully seeded {len(ids)} knowledge chunks into Chroma.")
        except Exception as e:
            logger.warning(f"Knowledge seeding notice: {e}")

    def query_knowledge(self, query: str, top_k: int = 4) -> List[SourceCitation]:
        """Perform semantic search against Lenny knowledge base with logging and empty results handling."""
        try:
            count = self.collection.count()
            if count == 0:
                logger.warning("⚠️ [Empty RAG Collection] Knowledge base is empty (0 documents in Chroma). No citations to retrieve.")
                return []

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
            )

            citations: List[SourceCitation] = []
            if results and results.get("documents") and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0] if results.get("distances") else []

                for idx, doc in enumerate(docs):
                    meta = metadatas[idx] if idx < len(metadatas) else {}
                    dist = distances[idx] if idx < len(distances) else None
                    score = round(max(0.0, 1.0 - dist), 4) if dist is not None else None

                    # Filter out chunks that do not meet semantic relevance threshold
                    if score is not None and score < settings.RAG_MIN_RELEVANCE_SCORE:
                        continue

                    citations.append(
                        SourceCitation(
                            title=meta.get("title", "Growth Playbook"),
                            source=meta.get("source", "Knowledge Base"),
                            content=doc,
                            relevance_score=score,
                            metadata=meta,
                        )
                    )

            if citations:
                logger.info(f"📚 [RAG Retrieved] Retrieved {len(citations)} knowledge chunks for query: '{query[:60]}...'")
            else:
                logger.info(f"ℹ️ [Empty RAG Results] 0 knowledge chunks matched query: '{query[:60]}...'. Baseline growth heuristics will be used.")

            return citations
        except Exception as e:
            logger.error(f"❌ [RAG Vector Error] Vector search query failed: {e}", exc_info=True)
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


_vector_service_instance: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    global _vector_service_instance
    if _vector_service_instance is None:
        _vector_service_instance = VectorService()
    return _vector_service_instance
