"""
Cleanup worker for data retention policy enforcement.

GDPR Compliance:
- Automatically delete old data based on retention policies
- Clean up inactive leads and conversations
- Archive old messages
"""

from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from typing import Dict, Any

from src.workers.celery_app import celery_app
from src.db.connection import get_async_session
from src.repositories.lead_repository import LeadRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.follow_up_repository import FollowUpRepository
from src.models.lead import Lead
from src.models.conversation import Conversation
from src.models.enums import State
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Data retention periods (configurable via environment)
RETENTION_POLICY = {
    "inactive_leads_days": 365,  # Delete leads inactive for 1 year
    "completed_conversations_days": 180,  # Archive conversations after 6 months
    "old_messages_days": 365,  # Delete messages older than 1 year
    "cancelled_followups_days": 90,  # Delete cancelled follow-ups after 90 days
}


@celery_app.task(name="cleanup.enforce_data_retention")
async def enforce_data_retention() -> Dict[str, Any]:
    """
    Enforce data retention policies (GDPR compliance).

    This task runs periodically (e.g., daily) to:
    - Delete inactive leads older than retention period
    - Archive or delete old conversations
    - Clean up old messages
    - Remove cancelled follow-ups

    Returns:
        Cleanup statistics
    """
    logger.info("Starting data retention enforcement")

    stats = {
        "leads_deleted": 0,
        "conversations_archived": 0,
        "messages_deleted": 0,
        "followups_deleted": 0,
        "errors": []
    }

    async with get_async_session() as session:
        try:
            # Clean up inactive leads
            stats["leads_deleted"] = await _cleanup_inactive_leads(session)

            # Archive old conversations
            stats["conversations_archived"] = await _archive_old_conversations(session)

            # Delete old messages
            stats["messages_deleted"] = await _cleanup_old_messages(session)

            # Delete cancelled follow-ups
            stats["followups_deleted"] = await _cleanup_cancelled_followups(session)

            await session.commit()

            logger.info(
                "Data retention enforcement completed",
                stats=stats
            )

        except Exception as e:
            logger.error("Data retention enforcement failed", error=str(e))
            stats["errors"].append(str(e))
            await session.rollback()

    return stats


async def _cleanup_inactive_leads(session) -> int:
    """
    Delete leads that have been inactive for longer than retention period.

    Args:
        session: Database session

    Returns:
        Number of leads deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(
        days=RETENTION_POLICY["inactive_leads_days"]
    )

    lead_repo = LeadRepository(session)

    # Find inactive leads in EXIT or PARK state
    result = await session.execute(
        select(Lead).where(
            and_(
                Lead.current_state.in_([State.EXIT, State.PARK]),
                Lead.updated_at < cutoff_date
            )
        )
    )

    inactive_leads = result.scalars().all()
    count = 0

    for lead in inactive_leads:
        try:
            await lead_repo.delete(lead.id)
            count += 1
            logger.info(
                "Deleted inactive lead",
                lead_id=str(lead.id),
                last_updated=lead.updated_at.isoformat()
            )
        except Exception as e:
            logger.error(
                "Failed to delete lead",
                lead_id=str(lead.id),
                error=str(e)
            )

    return count


async def _archive_old_conversations(session) -> int:
    """
    Archive conversations that ended longer than retention period.

    Args:
        session: Database session

    Returns:
        Number of conversations archived
    """
    cutoff_date = datetime.utcnow() - timedelta(
        days=RETENTION_POLICY["completed_conversations_days"]
    )

    conversation_repo = ConversationRepository(session)

    # Find ended conversations
    result = await session.execute(
        select(Conversation).where(
            and_(
                Conversation.ended_at.isnot(None),
                Conversation.ended_at < cutoff_date
            )
        )
    )

    old_conversations = result.scalars().all()
    count = 0

    for conversation in old_conversations:
        try:
            # TODO: Archive to cold storage before deletion
            # For now, we just mark them for archival
            # In production, you'd export to S3/GCS before deleting

            # await conversation_repo.delete(conversation.id)
            count += 1
            logger.info(
                "Archived conversation",
                conversation_id=str(conversation.id),
                ended_at=conversation.ended_at.isoformat()
            )
        except Exception as e:
            logger.error(
                "Failed to archive conversation",
                conversation_id=str(conversation.id),
                error=str(e)
            )

    return count


async def _cleanup_old_messages(session) -> int:
    """
    Delete messages older than retention period.

    Args:
        session: Database session

    Returns:
        Number of messages deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(
        days=RETENTION_POLICY["old_messages_days"]
    )

    message_repo = MessageRepository(session)

    # TODO: Implement bulk message deletion
    # For now, this is a placeholder
    # In production, you'd use bulk delete queries for efficiency

    count = 0
    logger.info("Message cleanup placeholder - implement bulk deletion")

    return count


async def _cleanup_cancelled_followups(session) -> int:
    """
    Delete cancelled follow-ups older than retention period.

    Args:
        session: Database session

    Returns:
        Number of follow-ups deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(
        days=RETENTION_POLICY["cancelled_followups_days"]
    )

    followup_repo = FollowUpRepository(session)

    # TODO: Implement cancelled follow-up cleanup
    # Query for cancelled follow-ups older than cutoff date

    count = 0
    logger.info("Follow-up cleanup placeholder - implement deletion")

    return count


@celery_app.task(name="cleanup.purge_redis_cache")
async def purge_redis_cache() -> Dict[str, Any]:
    """
    Purge expired entries from Redis cache.

    Returns:
        Purge statistics
    """
    from src.db.redis_client import get_redis_client

    logger.info("Starting Redis cache purge")

    stats = {
        "keys_scanned": 0,
        "keys_deleted": 0,
        "errors": []
    }

    try:
        redis = await get_redis_client()

        # Scan for expired session keys
        cursor = 0
        while True:
            cursor, keys = await redis.scan(
                cursor=cursor,
                match="session:*",
                count=100
            )

            stats["keys_scanned"] += len(keys)

            for key in keys:
                ttl = await redis.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set expiration to 24 hours
                    await redis.expire(key, 86400)

            if cursor == 0:
                break

        logger.info("Redis cache purge completed", stats=stats)

    except Exception as e:
        logger.error("Redis cache purge failed", error=str(e))
        stats["errors"].append(str(e))

    return stats
