from sqlalchemy import Column, Boolean, Integer, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import State


class Conversation(Base):
    """Conversation model representing a message exchange session."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)

    # State management
    current_state = Column(SQLEnum(State), nullable=False, default=State.GREETING, index=True)
    previous_state = Column(SQLEnum(State), nullable=True)

    # Bot/human control
    is_bot_active = Column(Boolean, nullable=False, default=True, index=True)
    human_takeover_at = Column(DateTime, nullable=True)
    human_agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Conversation metrics
    proof_asset_count = Column(Integer, nullable=False, default=0)
    message_count = Column(Integer, nullable=False, default=0)

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    state_transitions = relationship("StateTransition", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, lead_id={self.lead_id}, state={self.current_state})>"
