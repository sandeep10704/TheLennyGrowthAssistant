from fastapi import APIRouter, Depends, status
from models.schemas import ChatRequest, ChatResponse, SessionDetailResponse
from services.chat_service import ChatService, get_chat_service
from services.session_service import SessionService, get_session_service

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Session-based chat using session_id. Maintains conversational context and grounds answers in Lenny's Growth Playbooks using Chroma vector retrieval.",
)
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Session-based chat endpoint:
    - Accepts `message` and optional `session_id`
    - Creates or continues session context
    - Retrieves relevant knowledge citations from Chroma
    - Executes generation via OpenAI or Ollama
    - Stores messages in session history
    """
    return await chat_service.process_chat(request)


@router.get(
    "/chat/sessions",
    summary="List all recent chat sessions",
    description="Retrieves a list of recent conversation sessions ordered by last active update.",
)
async def list_recent_sessions(
    limit: int = 20,
    session_service: SessionService = Depends(get_session_service),
):
    """List recent conversation sessions."""
    return await session_service.list_sessions(limit=limit)


@router.get(
    "/chat/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details and message history",
)
async def get_session_history(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """Retrieve full message history for a given session_id."""
    return await session_service.get_session_details(session_id)


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session",
)
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """Delete a chat session and its associated conversation history."""
    await session_service.delete_session(session_id)
    return None
