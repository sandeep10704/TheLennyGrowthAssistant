import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.api.deps import get_db_session, get_assistant_service
from app.services.assistant import LennyGrowthAssistant
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationRead,
    ConversationDetail,
    ConversationCreate,
)
from app.db.models.conversation import Conversation
from app.db.models.message import Message

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def send_chat_message(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    assistant: LennyGrowthAssistant = Depends(get_assistant_service),
):
    """
    Send a message to Lenny Growth Assistant.
    Retrieves context from Chroma vector store, calls LLM, and persists chat history.
    """
    conversation_id = payload.conversation_id

    # 1. Fetch or create conversation
    if conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
    else:
        # Auto-title from the first prompt
        title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
        )
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # 2. Extract recent history
    history = []
    if conversation.messages:
        for m in conversation.messages:
            history.append({"role": m.role, "content": m.content})

    # 3. Store user message in DB
    user_msg_id = str(uuid.uuid4())
    user_message = Message(
        id=user_msg_id,
        conversation_id=conversation_id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    await db.flush()

    # 4. Generate AI response via LennyGrowthAssistant
    assistant_msg_id = str(uuid.uuid4())
    response: ChatResponse = await assistant.generate_growth_advice(
        query=payload.message,
        conversation_id=conversation_id,
        message_id=assistant_msg_id,
        chat_history=history,
        provider=payload.provider,
        model=payload.model,
        top_k=payload.top_k_sources or 4,
        temperature=payload.temperature or 0.7,
    )

    # 5. Persist assistant message in DB
    assistant_message = Message(
        id=assistant_msg_id,
        conversation_id=conversation_id,
        role="assistant",
        content=response.content,
        sources=[s.model_dump() for s in response.sources],
        model_used=f"{response.provider}:{response.model}",
    )
    db.add(assistant_message)
    await db.commit()

    return response


@router.get("/conversations", response_model=List[ConversationRead], tags=["Conversations"])
async def list_conversations(
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
):
    """List recent chat conversations."""
    result = await db.execute(
        select(Conversation)
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/conversations", response_model=ConversationRead, tags=["Conversations"])
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Explicitly create a new conversation."""
    new_conv = Conversation(
        id=str(uuid.uuid4()),
        title=payload.title or "New Growth Chat",
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return new_conv


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail, tags=["Conversations"])
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get conversation details and full message history."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Conversations"])
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    await db.delete(conversation)
    await db.commit()
    return None
