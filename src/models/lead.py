from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import State


class Lead(Base):
    """Lead model representing a potential client."""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Qualification data
    project_type = Column(String(100), nullable=True)
    budget = Column(String(100), nullable=True)
    budget_numeric = Column(Integer, nullable=True)
    timeline = Column(String(100), nullable=True)
    business_type = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)

    # State and behavior
    current_state = Column(SQLEnum(State), nullable=False, default=State.GREETING, index=True)
    budget_avoidance_count = Column(Integer, nullable=False, default=0)

    # Agent assignment
    assigned_agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Flexible metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    scores = relationship("LeadScore", back_populates="lead", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, phone={self.phone_number}, state={self.current_state})>"
