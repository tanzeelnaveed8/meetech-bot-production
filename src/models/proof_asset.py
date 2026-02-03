from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.models import Base
from src.models.enums import AssetType


class ProofAsset(Base):
    """ProofAsset model for portfolio items, case studies, and testimonials."""

    __tablename__ = "proof_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset details
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    project_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Content
    content_url = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProofAsset(id={self.id}, type={self.asset_type}, title={self.title})>"
