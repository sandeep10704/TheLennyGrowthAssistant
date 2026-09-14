import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from config.settings import logger
from models.schemas import ChatRequest, ChatResponse, SourceCitation
from services.session_service import SessionService, get_session_service
from services.vector_service import VectorService, get_vector_service
from services.llm_service import LLMService, get_llm_service

LENNY_SYSTEM_PROMPT = """You are Lenny Growth Assistant, an executive product & growth advisor modeled after Lenny Rachitsky's product frameworks, newsletter, and podcast.

Your mission is to help founders, product leaders, and growth practitioners make sound, grounded strategic and tactical decisions.

Core Heuristics & Rules:
1. Ground your advice in real-world benchmarks, growth loops, and proven heuristics (e.g., Sean Ellis PMF test, retention curves, Aha! moments, North Star metrics).
2. Prioritize retention and customer value over vanity acquisition.
3. Be structured, direct, highly practical, and empathetic. Use bullet points and clear sections.
4. Maintain conversational context from prior messages in this session.
5. If relevant knowledge snippets from Lenny's playbooks are provided below, incorporate them naturally into your recommendations.

--- RELEVANT KNOWLEDGE BASE ---
{context}
-------------------------------
"""


class ChatService:
    """Core chat orchestration service coordinating sessions, vectors, and LLM inference."""

    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        vector_service: Optional[VectorService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.session_service = session_service or get_session_service()
        self.vector_service = vector_service or get_vector_service()
        self.llm_service = llm_service or get_llm_service()

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a conversational turn in a session."""
        # 1. Resolve or generate session_id
        session_id = await self.session_service.get_or_create_session(
            session_id=request.session_id,
            title=request.message[:40] + ("..." if len(request.message) > 40 else ""),
        )

        # 2. Persist user message in session history
        await self.session_service.add_user_message(
            session_id=session_id,
            content=request.message,
        )

        # 3. Retrieve relevant knowledge chunks from vector store
        sources: List[SourceCitation] = self.vector_service.query_knowledge(
            query=request.message,
            top_k=request.top_k_sources or 4,
        )

        # 4. Format context block
        if sources:
            context_blocks = []
            for i, src in enumerate(sources):
                context_blocks.append(f"[{i+1}] {src.title}:\n{src.content}")
            context_text = "\n\n".join(context_blocks)
        else:
            context_text = "No direct playbook matches found. Rely on general Lenny Rachitsky growth heuristics."

        # 5. Fetch recent conversational history for memory
        history = await self.session_service.get_session_history(session_id=session_id, limit=8)

        # 6. Construct prompt messages
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": LENNY_SYSTEM_PROMPT.format(context=context_text)}
        ]

        # Add history (excluding the very last user message since we'll add it explicitly)
        if len(history) > 1:
            for item in history[:-1]:
                messages.append({"role": item["role"], "content": item["content"]})

        messages.append({"role": "user", "content": request.message})

        # 7. Execute LLM generation
        result = await self.llm_service.generate_response(
            messages=messages,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature or 0.7,
        )

        response_content = result["content"]
        provider_used = result["provider"]
        model_used = result["model"]

        # 8. Persist assistant response in session history
        message_id = await self.session_service.add_assistant_message(
            session_id=session_id,
            content=response_content,
            sources=sources,
            model_used=f"{provider_used}:{model_used}",
        )

        # 9. Return structured response
        return ChatResponse(
            session_id=session_id,
            message_id=message_id,
            role="assistant",
            content=response_content,
            sources=sources,
            provider=provider_used,
            model=model_used,
            created_at=datetime.now(timezone.utc),
        )


_chat_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
