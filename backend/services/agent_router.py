import re
import uuid
from typing import Dict, Any, Optional, Tuple, Literal
from config.settings import logger
from models.schemas import (
    AgentRouterRequest,
    AgentRouterResponse,
    AnswerData,
    EssayData,
    ArtifactData,
    SourceCitation,
)
from services.vector_service import VectorService, get_vector_service
from services.session_service import SessionService, get_session_service
from services.llm_service import LLMService, get_llm_service
from services.essay_generator import generate_ship30_article, Ship30Article
from services.artifact_generator import generate_artifact, ArtifactResponse

IntentType = Literal["answer", "essay", "artifact"]

# Regex patterns for fast, deterministic intent classification
ESSAY_PATTERNS = [
    r"\b(?:write|draft|compose)\s+(?:an?\s+)?(?:article|essay|deep[- ]dive|newsletter|guide|post|piece)\b",
    r"\b(?:article|essay)\s+(?:on|about|explaining|covering)\b",
]

ARTIFACT_PATTERNS = [
    r"\b(?:create|build|generate|design|make)\s+(?:an?\s+)?(?:page|webpage|landing\s+page|ui|dashboard|calculator|tool|spec)\b",
    r"\b(?:landing\s+page|dashboard\s+page|ui\s+component)\s+(?:for|about)\b",
]


class AgentRouter:
    """
    Intelligent Agent Router:
    Classifies user intent into:
    - 'answer' (RAG question answering)
    - 'essay'  (Long-form essay/article synthesis)
    - 'artifact' (Interactive page/code artifact generation)

    Returns structured output:
    {
      "type": "answer" | "essay" | "artifact",
      "data": ...
    }
    """

    def __init__(
        self,
        vector_service: Optional[VectorService] = None,
        session_service: Optional[SessionService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.vector_service = vector_service or get_vector_service()
        self.session_service = session_service or get_session_service()
        self.llm_service = llm_service or get_llm_service()

    def classify_intent(self, prompt: str) -> Tuple[IntentType, float]:
        """
        Classifies prompt intent based on semantic patterns:
        - "write article" -> essay
        - "create page" -> artifact
        - questions / others -> answer (RAG)
        """
        clean_prompt = prompt.strip().lower()

        # 1. Check for Essay / Article Generation Intent
        for pattern in ESSAY_PATTERNS:
            if re.search(pattern, clean_prompt):
                logger.info(f"Classified intent as 'essay' via pattern match: '{clean_prompt[:50]}...'")
                return "essay", 0.98

        # 2. Check for Page / Artifact Generation Intent
        for pattern in ARTIFACT_PATTERNS:
            if re.search(pattern, clean_prompt):
                logger.info(f"Classified intent as 'artifact' via pattern match: '{clean_prompt[:50]}...'")
                return "artifact", 0.98

        # 3. Default to RAG Question Answering Intent
        logger.info(f"Classified intent as 'answer' (RAG): '{clean_prompt[:50]}...'")
        return "answer", 0.95

    async def route_and_execute(self, request: AgentRouterRequest) -> AgentRouterResponse:
        """
        Routes the prompt to the appropriate generator and returns structured output:
        {
          "type": "answer" | "essay" | "artifact",
          "data": ...
        }
        """
        prompt = request.prompt.strip()
        intent, confidence = self.classify_intent(prompt)

        if intent == "essay":
            data = await self._handle_essay(
                prompt=prompt,
                provider=request.provider,
                model=request.model,
                temperature=request.temperature or 0.7,
            )
            return AgentRouterResponse(type="essay", data=data)

        elif intent == "artifact":
            data = await self._handle_artifact(
                prompt=prompt,
                provider=request.provider,
                model=request.model,
                temperature=request.temperature or 0.6,
            )
            return AgentRouterResponse(type="artifact", data=data)

        else:
            data = await self._handle_answer(
                query=prompt,
                session_id=request.session_id,
                provider=request.provider,
                model=request.model,
                temperature=request.temperature or 0.7,
            )
            return AgentRouterResponse(type="answer", data=data)

    # --------------------------------------------------------------------------
    # Intent 1: Question -> RAG Answer Generator
    # --------------------------------------------------------------------------
    async def _handle_answer(
        self,
        query: str,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AnswerData:
        # 1. Resolve session
        sid = await self.session_service.get_or_create_session(
            session_id=session_id,
            title=query[:40] + ("..." if len(query) > 40 else ""),
        )
        await self.session_service.add_user_message(session_id=sid, content=query)

        # 2. Retrieve top-5 knowledge chunks from Chroma
        sources: List[SourceCitation] = self.vector_service.query_knowledge(query=query, top_k=5)

        context_text = "\n\n".join(
            f"[{i+1}] {s.title} ({s.source}):\n{s.content}" for i, s in enumerate(sources)
        ) if sources else "Rely on proven Lenny Rachitsky product and growth heuristics."

        # 3. Generate grounded answer
        content = await self.llm_service.generate_response(
            query=query,
            context=context_text,
            provider=provider,
            model=model,
            temperature=temperature,
        )

        provider_used = provider or "openai"
        model_used = model or "gpt-4o"

        # 4. Persist to session
        await self.session_service.add_assistant_message(
            session_id=sid,
            content=content,
            sources=sources,
            model_used=f"{provider_used}:{model_used}",
        )

        return AnswerData(
            query=query,
            content=content,
            sources=sources,
            session_id=sid,
            provider=provider_used,
            model=model_used,
        )

    # --------------------------------------------------------------------------
    # Intent 2: "write article" -> Essay Generator
    # --------------------------------------------------------------------------
    async def _handle_essay(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.75,
    ) -> EssayData:
        # Clean topic text
        topic = re.sub(
            r"^(?:please\s+)?(?:write|draft|compose)\s+(?:an?\s+)?(?:article|essay|deep[- ]dive|newsletter|guide)\s+(?:on|about|explaining)?\s*",
            "",
            prompt,
            flags=re.IGNORECASE,
        ).strip() or prompt

        # Retrieve background knowledge for factual grounding
        sources = self.vector_service.query_knowledge(query=topic, top_k=5)
        context_str = "\n\n".join(s.content for s in sources) if sources else "Standard high-growth frameworks."

        # Generate article using Ship 30 framework (outline -> expand -> format)
        article: Ship30Article = await generate_ship30_article(
            context=context_str,
            topic=topic,
            llm_service=self.llm_service,
        )

        return EssayData(
            title=article.title,
            subtitle=article.subtitle,
            summary=f"A ~{article.word_count}-word Ship 30 essay on {topic}, synthesized from growth frameworks.",
            content=article.content,
            estimated_read_time_mins=max(3, article.word_count // 200),
            frameworks_referenced=["Retention Curves", "Sean Ellis PMF Benchmark", "Growth Loops", "Aha! Moments"],
            takeaways=article.takeaways,
            provider=provider or "openai",
            model=model or "gpt-4o",
        )

    # --------------------------------------------------------------------------
    # Intent 3: "create page" -> Artifact Generator
    # --------------------------------------------------------------------------
    async def _handle_artifact(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.6,
    ) -> ArtifactData:
        # Extract spec description
        spec = re.sub(
            r"^(?:please\s+)?(?:create|build|generate|design|make)\s+(?:an?\s+)?(?:page|webpage|landing\s+page|ui|dashboard|calculator|spec|checklist)\s+(?:for|about)?\s*",
            "",
            prompt,
            flags=re.IGNORECASE,
        ).strip() or prompt

        # Generate artifact using ArtifactGenerator (auto-detects HTML vs Markdown)
        artifact_res: ArtifactResponse = await generate_artifact(
            prompt=prompt,
            output_type=None,
            provider=provider,
            model=model,
        )

        if artifact_res.type == "html":
            title = f"{spec.title()} Page"
            title_extract = re.search(r"<title>(.*?)</title>", artifact_res.content, re.IGNORECASE)
            if title_extract:
                title = title_extract.group(1).strip()
            artifact_type = "landing_page"
            description = f"Interactive responsive web page generated for '{spec}' with Tailwind CSS."
            metadata = {"framework": "HTML5 + Tailwind CSS", "type": "html", "interactive": True}
        else:
            title = f"{spec.title()} Specification"
            title_extract = re.search(r"^#\s+(.+)$", artifact_res.content, re.MULTILINE)
            if title_extract:
                title = title_extract.group(1).strip()
            artifact_type = "markdown_spec"
            description = f"Structured Markdown specification/checklist generated for '{spec}'."
            metadata = {"framework": "GitHub Flavored Markdown", "type": "markdown", "interactive": False}

        return ArtifactData(
            title=title,
            artifact_type=artifact_type,
            description=description,
            code=artifact_res.content,
            metadata=metadata,
            provider=provider or "openai",
            model=model or "gpt-4o",
        )


_agent_router_instance: Optional[AgentRouter] = None


def get_agent_router() -> AgentRouter:
    global _agent_router_instance
    if _agent_router_instance is None:
        _agent_router_instance = AgentRouter()
    return _agent_router_instance
