from sqlalchemy import Column, Integer, Boolean, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import ScoreCategory


class LeadScore(Base):
    """LeadScore model representing calculated lead quality assessment."""

    __tablename__ = "lead_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)

    # Score components
    total_score = Column(Integer, nullable=False)
    budget_score = Column(Integer, nullable=False)
    timeline_score = Column(Integer, nullable=False)
    clarity_score = Column(Integer, nullable=False)
    country_score = Column(Integer, nullable=False)
    behavior_score = Column(Integer, nullable=False)

    # Score category
    score_category = Column(SQLEnum(ScoreCategory), nullable=False, index=True)

    # Metadata
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reasoning = Column(Text, nullable=True)
    triggered_handover = Column(Boolean, nullable=False, default=False, index=True)

    # Relationships
    lead = relationship("Lead", back_populates="scores")

    def __repr__(self) -> str:
        return f"<LeadScore(id={self.id}, total={self.total_score}, category={self.score_category})>"
