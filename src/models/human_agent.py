from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.models import Base


class HumanAgent(Base):
    """HumanAgent model representing sales team members."""

    __tablename__ = "human_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent details
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Availability
    is_available = Column(Boolean, nullable=False, default=True, index=True)
    max_concurrent_conversations = Column(Integer, nullable=False, default=5)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<HumanAgent(id={self.id}, name={self.name}, available={self.is_available})>"
