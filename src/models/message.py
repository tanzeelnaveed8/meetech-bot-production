from sqlalchemy import Column, String, Text, Float, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import Sender, MessageType


class Message(Base):
    """Message model representing individual messages in a conversation."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # Message details
    sender = Column(SQLEnum(Sender), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    message_type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.TEXT)

    # Intent detection
    detected_intent = Column(String(100), nullable=True)
    intent_confidence = Column(Float, nullable=True)

    # WhatsApp integration
    whatsapp_message_id = Column(String(255), unique=True, nullable=True, index=True)

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender={self.sender}, intent={self.detected_intent})>"
