from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.message import Message
from src.models.enums import Sender, MessageType


class MessageRepository:
    """Repository for Message CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: UUID,
        sender: Sender,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        detected_intent: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        whatsapp_message_id: Optional[str] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            message_type=message_type,
            detected_intent=detected_intent,
            intent_confidence=intent_confidence,
            whatsapp_message_id=whatsapp_message_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID."""
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_by_whatsapp_id(self, whatsapp_message_id: str) -> Optional[Message]:
        """Get message by WhatsApp message ID (for deduplication)."""
        result = await self.session.execute(
            select(Message).where(Message.whatsapp_message_id == whatsapp_message_id)
        )
        return result.scalar_one_or_none()

    async def list_by_conversation(
        self, conversation_id: UUID, limit: int = 100
    ) -> List[Message]:
        """List messages for a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last_message(self, conversation_id: UUID) -> Optional[Message]:
        """Get the last message in a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
