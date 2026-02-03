from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from src.db.connection import get_db
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.lead_repository import LeadRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.human_agent_repository import HumanAgentRepository
from src.services.handover_service import HandoverService
from src.models.enums import State, Sender
from src.integrations.whatsapp_client import get_whatsapp_client
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic models for request/response
class ConversationSummary(BaseModel):
    conversation_id: str
    lead_id: str
    lead_phone: str
    current_state: str
    started_at: str
    last_message_at: Optional[str]
    message_count: int
    is_bot_active: bool
    assigned_agent_name: Optional[str]
    lead_score: Optional[dict]


class SendMessageRequest(BaseModel):
    content: str


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    email: str
    is_available: bool
    active_conversations: int
    max_concurrent_conversations: int


@router.get("/agent/conversations", response_model=dict)
async def list_conversations(
    status: str = Query("active", enum=["active", "pending_handover", "assigned_to_me", "all"]),
    score_category: Optional[str] = Query(None, enum=["LOW", "MEDIUM", "HIGH"]),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_db)
):
    """
    List conversations for agent dashboard.

    Args:
        status: Filter by status
        score_category: Filter by score category
        limit: Maximum results
        offset: Pagination offset
        session: Database session

    Returns:
        List of conversations
    """
    try:
        conversation_repo = ConversationRepository(session)

        if status == "active":
            conversations = await conversation_repo.list_active(limit)
        elif status == "pending_handover":
            conversations = await conversation_repo.list_pending_handover(limit)
        else:
            # TODO: Implement other filters
            conversations = await conversation_repo.list_active(limit)

        # TODO: Apply score_category filter
        # TODO: Implement pagination with offset

        return {
            "conversations": [],  # TODO: Convert to ConversationSummary
            "total": len(conversations),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error("Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    Get full conversation details with history.

    Args:
        conversation_id: Conversation ID
        session: Database session

    Returns:
        Conversation details with messages and score
    """
    try:
        handover_service = HandoverService(session)
        context = await handover_service.get_handover_context(conversation_id)

        return context

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get conversation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/conversations/{conversation_id}/takeover")
async def takeover_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    Take over conversation from bot (FR-011).

    Args:
        conversation_id: Conversation ID
        session: Database session

    Returns:
        Takeover confirmation
    """
    try:
        # TODO: Get agent_id from JWT token
        agent_id = UUID("00000000-0000-0000-0000-000000000001")  # Mock for now

        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.takeover(conversation_id, agent_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info(
            "Conversation taken over",
            conversation_id=str(conversation_id),
            agent_id=str(agent_id)
        )

        return {
            "status": "takeover_successful",
            "conversation_id": str(conversation.id),
            "agent_id": str(agent_id),
            "takeover_at": conversation.human_takeover_at.isoformat() if conversation.human_takeover_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Takeover failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/conversations/{conversation_id}/release")
async def release_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    Release conversation back to bot.

    Args:
        conversation_id: Conversation ID
        session: Database session

    Returns:
        Release confirmation
    """
    try:
        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.release(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info("Conversation released", conversation_id=str(conversation_id))

        return {
            "status": "release_successful",
            "conversation_id": str(conversation.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Release failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/conversations/{conversation_id}/messages")
async def send_agent_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Send message as human agent.

    Args:
        conversation_id: Conversation ID
        request: Message content
        session: Database session

    Returns:
        Message sent confirmation
    """
    try:
        conversation_repo = ConversationRepository(session)
        message_repo = MessageRepository(session)
        lead_repo = LeadRepository(session)

        # Get conversation
        conversation = await conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Verify agent has control
        if conversation.is_bot_active:
            raise HTTPException(
                status_code=403,
                detail="Agent does not have control of this conversation"
            )

        # Get lead
        lead = await lead_repo.get_by_id(conversation.lead_id)

        # Store message
        message = await message_repo.create(
            conversation.id,
            Sender.HUMAN,
            request.content
        )

        # Send via WhatsApp
        whatsapp_client = get_whatsapp_client()
        await whatsapp_client.send_message(lead.phone_number, request.content)

        logger.info(
            "Agent message sent",
            conversation_id=str(conversation_id),
            message_id=str(message.id)
        )

        return {
            "message_id": str(message.id),
            "sent_at": message.timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send agent message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/leads/{lead_id}")
async def get_lead(
    lead_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    Get lead details with score.

    Args:
        lead_id: Lead ID
        session: Database session

    Returns:
        Lead details
    """
    try:
        from src.repositories.lead_score_repository import LeadScoreRepository

        lead_repo = LeadRepository(session)
        score_repo = LeadScoreRepository(session)

        lead = await lead_repo.get_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        latest_score = await score_repo.get_latest_by_lead(lead_id)

        return {
            "lead_id": str(lead.id),
            "phone_number": lead.phone_number,
            "created_at": lead.created_at.isoformat(),
            "project_type": lead.project_type,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "business_type": lead.business_type,
            "country": lead.country,
            "current_state": lead.current_state.value,
            "latest_score": {
                "total": latest_score.total_score,
                "category": latest_score.score_category.value,
                "reasoning": latest_score.reasoning,
            } if latest_score else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/me", response_model=AgentInfo)
async def get_current_agent(
    session: AsyncSession = Depends(get_db)
):
    """
    Get current agent information.

    Args:
        session: Database session

    Returns:
        Agent info
    """
    # TODO: Get agent from JWT token
    # For now, return mock data
    return AgentInfo(
        agent_id="00000000-0000-0000-0000-000000000001",
        name="Mock Agent",
        email="agent@example.com",
        is_available=True,
        active_conversations=0,
        max_concurrent_conversations=5
    )


@router.patch("/agent/me")
async def update_agent_availability(
    is_available: bool,
    session: AsyncSession = Depends(get_db)
):
    """
    Update agent availability status.

    Args:
        is_available: Availability status
        session: Database session

    Returns:
        Updated agent info
    """
    # TODO: Implement with real agent from JWT
    return {"status": "updated", "is_available": is_available}
