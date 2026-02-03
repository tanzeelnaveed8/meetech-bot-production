from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.lead import Lead
from src.models.enums import State


class LeadRepository:
    """Repository for Lead CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, phone_number: str) -> Lead:
        """Create a new lead."""
        lead = Lead(phone_number=phone_number, current_state=State.GREETING)
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def get_by_id(self, lead_id: UUID) -> Optional[Lead]:
        """Get lead by ID."""
        result = await self.session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> Optional[Lead]:
        """Get lead by phone number."""
        result = await self.session.execute(
            select(Lead).where(Lead.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def update(self, lead: Lead) -> Lead:
        """Update lead."""
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def delete(self, lead_id: UUID) -> None:
        """Delete lead (GDPR compliance)."""
        lead = await self.get_by_id(lead_id)
        if lead:
            await self.session.delete(lead)
            await self.session.flush()

    async def list_by_state(self, state: State, limit: int = 100) -> List[Lead]:
        """List leads by current state."""
        result = await self.session.execute(
            select(Lead).where(Lead.current_state == state).limit(limit)
        )
        return list(result.scalars().all())

    async def increment_budget_avoidance(self, lead_id: UUID) -> Lead:
        """Increment budget avoidance count."""
        lead = await self.get_by_id(lead_id)
        if lead:
            lead.budget_avoidance_count += 1
            await self.session.flush()
        return lead
