from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.services.vector_store import get_vector_store
from app.services.llm.factory import get_llm_service
from app.schemas.chat import ChatResponse, SourceCitation
from app.core.config import settings
from app.core.logging import logger

SYSTEM_PROMPT = """You are Lenny Growth Assistant, an AI advisor modeled after Lenny Rachitsky's product & growth frameworks, newsletters, and podcast interviews.

Your goal is to help founders, product leaders, and growth practitioners make sound strategic and tactical decisions.

Core Guidance:
1. Ground your advice in real-world benchmarks, growth loops, and proven heuristics (e.g., Sean Ellis PMF survey, retention curves, Aha! moments, North Star metrics).
2. Prioritize retention and customer value over vanity acquisition.
3. Be direct, structured, practical, and highly empathetic to the challenges of building products.
4. If relevant context from Lenny's knowledge base is provided below, incorporate it thoughtfully and reference its principles.

--- RELEVANT KNOWLEDGE CONTEXT ---
{context}
---------------------------------
"""


class LennyGrowthAssistant:
    def __init__(self):
        self.vector_store = get_vector_store()

    async def generate_growth_advice(
        self,
        query: str,
        conversation_id: str,
        message_id: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        top_k: int = 4,
        temperature: float = 0.7,
    ) -> ChatResponse:
        # 1. Retrieve knowledge from Chroma vector store
        relevant_chunks = self.vector_store.query_similar(query_text=query, n_results=top_k)

        # 2. Build context string
        if relevant_chunks:
            context_blocks = []
            for i, chunk in enumerate(relevant_chunks):
                title = chunk.get("title", "Resource")
                content = chunk.get("content", "")
                context_blocks.append(f"[{i+1}] {title}:\n{content}")
            context_str = "\n\n".join(context_blocks)
        else:
            context_str = "No specific playbook documents retrieved. Use general high-growth product best practices."

        # 3. Format messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context_str)}
        ]

        if chat_history:
            for hist in chat_history[-6:]:  # Keep recent history for context
                messages.append({"role": hist["role"], "content": hist["content"]})

        messages.append({"role": "user", "content": query})

        # 4. Resolve LLM provider & invoke
        target_provider = provider or settings.LLM_PROVIDER
        target_model = model or (settings.OPENAI_MODEL if target_provider == "openai" else settings.OLLAMA_MODEL)

        llm_service = get_llm_service(provider=target_provider)
        response_text = await llm_service.generate_response(
            messages=messages,
            model=target_model,
            temperature=temperature,
        )

        # 5. Format citations
        citations = [
            SourceCitation(
                title=chunk.get("title", "Growth Playbook"),
                source=chunk.get("source", "Knowledge Base"),
                content=chunk.get("content", ""),
                relevance_score=chunk.get("relevance_score"),
                metadata=chunk.get("metadata", {}),
            )
            for chunk in relevant_chunks
        ]

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            role="assistant",
            content=response_text,
            sources=citations,
            provider=target_provider,
            model=target_model,
            created_at=datetime.now(timezone.utc),
        )


_assistant_instance: Optional[LennyGrowthAssistant] = None


def get_assistant() -> LennyGrowthAssistant:
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = LennyGrowthAssistant()
    return _assistant_instance
