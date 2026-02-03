from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any, List
from uuid import UUID
import json
from datetime import datetime

from src.db.connection import get_db_session
from src.repositories.lead_repository import LeadRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.lead_score_repository import LeadScoreRepository
from src.repositories.follow_up_repository import FollowUpRepository

router = APIRouter(prefix="/gdpr")


# Request/Response Models
class DataDeletionRequest(BaseModel):
    """Request model for GDPR data deletion."""
    phone_number: str
    reason: str = "User requested data deletion"


class DataDeletionResponse(BaseModel):
    """Response model for data deletion."""
    phone_number: str
    deleted_at: str
    records_deleted: Dict[str, int]


class DataExportResponse(BaseModel):
    """Response model for data export."""
    phone_number: str
    exported_at: str
    data: Dict[str, Any]


# ============================================================================
# GDPR Data Deletion Endpoint (T121)
# ============================================================================

@router.delete("/data/{phone_number}", response_model=DataDeletionResponse)
async def delete_user_data(
    phone_number: str,
    request: DataDeletionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete all user data (GDPR Right to Erasure / Right to be Forgotten).

    This endpoint permanently deletes:
    - Lead record
    - All conversations
    - All messages
    - All lead scores
    - All follow-ups
    - All state transitions

    Args:
        phone_number: Phone number of the user
        request: Deletion request with reason
        db: Database session

    Returns:
        Deletion confirmation with counts
    """
    lead_repo = LeadRepository(db)
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    score_repo = LeadScoreRepository(db)
    followup_repo = FollowUpRepository(db)

    # Find lead by phone number
    lead = await lead_repo.get_by_phone(phone_number)

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for phone number {phone_number}"
        )

    records_deleted = {
        "leads": 0,
        "conversations": 0,
        "messages": 0,
        "scores": 0,
        "follow_ups": 0
    }

    # Get all conversations for this lead
    conversations = await conversation_repo.list_by_lead(lead.id)
    records_deleted["conversations"] = len(conversations)

    # Delete messages for each conversation
    for conversation in conversations:
        messages = await message_repo.list_by_conversation(conversation.id)
        records_deleted["messages"] += len(messages)

    # Delete lead scores
    scores = await score_repo.list_by_lead(lead.id)
    records_deleted["scores"] = len(scores)

    # Delete follow-ups
    follow_ups = await followup_repo.list_by_lead(lead.id)
    records_deleted["follow_ups"] = len(follow_ups)

    # Delete the lead (cascade will delete related records)
    await lead_repo.delete(lead.id)
    records_deleted["leads"] = 1

    # Commit the transaction
    await db.commit()

    return DataDeletionResponse(
        phone_number=phone_number,
        deleted_at=datetime.utcnow().isoformat(),
        records_deleted=records_deleted
    )


# ============================================================================
# GDPR Data Export Endpoint (T122)
# ============================================================================

@router.get("/data/{phone_number}", response_model=DataExportResponse)
async def export_user_data(
    phone_number: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Export all user data (GDPR Right to Data Portability).

    This endpoint exports:
    - Lead information
    - All conversations
    - All messages
    - All lead scores
    - All follow-ups

    Args:
        phone_number: Phone number of the user
        db: Database session

    Returns:
        Complete user data export in JSON format
    """
    lead_repo = LeadRepository(db)
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    score_repo = LeadScoreRepository(db)
    followup_repo = FollowUpRepository(db)

    # Find lead by phone number
    lead = await lead_repo.get_by_phone(phone_number)

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for phone number {phone_number}"
        )

    # Build complete data export
    export_data = {
        "lead": {
            "id": str(lead.id),
            "phone_number": lead.phone_number,
            "current_state": lead.current_state.value if lead.current_state else None,
            "project_type": lead.project_type,
            "budget_numeric": lead.budget_numeric,
            "budget_range": lead.budget_range,
            "timeline": lead.timeline,
            "business_type": lead.business_type,
            "country": lead.country,
            "budget_avoidance_count": lead.budget_avoidance_count,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
        },
        "conversations": [],
        "messages": [],
        "scores": [],
        "follow_ups": []
    }

    # Export conversations
    conversations = await conversation_repo.list_by_lead(lead.id)
    for conversation in conversations:
        export_data["conversations"].append({
            "id": str(conversation.id),
            "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "current_state": conversation.current_state.value if conversation.current_state else None,
            "is_bot_active": conversation.is_bot_active,
            "message_count": conversation.message_count,
            "proof_asset_count": conversation.proof_asset_count
        })

        # Export messages for this conversation
        messages = await message_repo.list_by_conversation(conversation.id)
        for message in messages:
            export_data["messages"].append({
                "id": str(message.id),
                "conversation_id": str(message.conversation_id),
                "sender": message.sender.value if message.sender else None,
                "message_type": message.message_type.value if message.message_type else None,
                "content": message.content,
                "detected_intent": message.detected_intent,
                "created_at": message.created_at.isoformat() if message.created_at else None
            })

    # Export lead scores
    scores = await score_repo.list_by_lead(lead.id)
    for score in scores:
        export_data["scores"].append({
            "id": str(score.id),
            "total_score": score.total_score,
            "score_category": score.score_category.value if score.score_category else None,
            "budget_score": score.budget_score,
            "timeline_score": score.timeline_score,
            "clarity_score": score.clarity_score,
            "country_score": score.country_score,
            "behavior_score": score.behavior_score,
            "reasoning": score.reasoning,
            "created_at": score.created_at.isoformat() if score.created_at else None
        })

    # Export follow-ups
    follow_ups = await followup_repo.list_by_lead(lead.id)
    for followup in follow_ups:
        export_data["follow_ups"].append({
            "id": str(followup.id),
            "scenario": followup.scenario.value if followup.scenario else None,
            "attempt": followup.attempt,
            "scheduled_at": followup.scheduled_at.isoformat() if followup.scheduled_at else None,
            "sent_at": followup.sent_at.isoformat() if followup.sent_at else None,
            "is_cancelled": followup.is_cancelled,
            "message_content": followup.message_content
        })

    return DataExportResponse(
        phone_number=phone_number,
        exported_at=datetime.utcnow().isoformat(),
        data=export_data
    )
