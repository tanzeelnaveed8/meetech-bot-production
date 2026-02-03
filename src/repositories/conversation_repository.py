from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.conversation import Conversation
from src.models.enums import State


class ConversationRepository:
    """Repository for Conversation CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, lead_id: UUID) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            lead_id=lead_id,
            current_state=State.GREETING,
            is_bot_active=True
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_lead(self, lead_id: UUID) -> Optional[Conversation]:
        """Get active conversation for a lead."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.lead_id == lead_id)
            .where(Conversation.ended_at.is_(None))
            .order_by(Conversation.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def update(self, conversation: Conversation) -> Conversation:
        """Update conversation."""
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def list_active(self, limit: int = 100) -> List[Conversation]:
        """List active conversations."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.ended_at.is_(None))
            .where(Conversation.is_bot_active == True)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_pending_handover(self, limit: int = 100) -> List[Conversation]:
        """List conversations pending human handover."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.current_state == State.HUMAN_HANDOVER)
            .where(Conversation.human_agent_id.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def takeover(self, conversation_id: UUID, agent_id: UUID) -> Conversation:
        """Mark conversation as taken over by human agent."""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.is_bot_active = False
            conversation.human_agent_id = agent_id
            from datetime import datetime
            conversation.human_takeover_at = datetime.utcnow()
            await self.session.flush()
        return conversation

    async def release(self, conversation_id: UUID) -> Conversation:
        """Release conversation back to bot."""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.is_bot_active = True
            await self.session.flush()
        return conversation
