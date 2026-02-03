from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import State


class StateTransition(Base):
    """StateTransition model for logging state machine transitions."""

    __tablename__ = "state_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # State transition details
    from_state = Column(SQLEnum(State), nullable=False, index=True)
    to_state = Column(SQLEnum(State), nullable=False, index=True)
    transitioned_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Trigger information
    trigger = Column(String(255), nullable=True)

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="state_transitions")

    def __repr__(self) -> str:
        return f"<StateTransition(id={self.id}, {self.from_state} -> {self.to_state})>"
