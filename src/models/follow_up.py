from sqlalchemy import Column, Text, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import FollowUpScenario


class FollowUp(Base):
    """FollowUp model for tracking automated follow-up messages."""

    __tablename__ = "follow_ups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)

    # Follow-up details
    trigger_scenario = Column(SQLEnum(FollowUpScenario), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)  # 1, 2, or 3

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True, index=True)

    # Response tracking
    lead_responded = Column(Boolean, nullable=False, default=False)
    response_at = Column(DateTime, nullable=True)

    # Status
    cancelled = Column(Boolean, nullable=False, default=False)

    # Message content
    message_content = Column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="follow_ups")

    def __repr__(self) -> str:
        return f"<FollowUp(id={self.id}, scenario={self.trigger_scenario}, attempt={self.attempt_number})>"
