from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from src.models.follow_up import FollowUp
from src.models.enums import FollowUpScenario


class FollowUpRepository:
    """Repository for FollowUp CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        lead_id: UUID,
        trigger_scenario: FollowUpScenario,
        attempt_number: int,
        scheduled_at: datetime,
        message_content: str
    ) -> FollowUp:
        """Create a new follow-up."""
        follow_up = FollowUp(
            lead_id=lead_id,
            trigger_scenario=trigger_scenario,
            attempt_number=attempt_number,
            scheduled_at=scheduled_at,
            message_content=message_content
        )
        self.session.add(follow_up)
        await self.session.flush()
        return follow_up

    async def get_by_id(self, follow_up_id: UUID) -> Optional[FollowUp]:
        """Get follow-up by ID."""
        result = await self.session.execute(
            select(FollowUp).where(FollowUp.id == follow_up_id)
        )
        return result.scalar_one_or_none()

    async def list_by_lead(self, lead_id: UUID) -> List[FollowUp]:
        """List all follow-ups for a lead."""
        result = await self.session.execute(
            select(FollowUp)
            .where(FollowUp.lead_id == lead_id)
            .order_by(FollowUp.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def get_pending_by_lead(self, lead_id: UUID) -> List[FollowUp]:
        """Get pending (not sent, not cancelled) follow-ups for a lead."""
        result = await self.session.execute(
            select(FollowUp)
            .where(
                and_(
                    FollowUp.lead_id == lead_id,
                    FollowUp.sent_at.is_(None),
                    FollowUp.cancelled == False
                )
            )
            .order_by(FollowUp.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def get_due_follow_ups(self, limit: int = 100) -> List[FollowUp]:
        """Get follow-ups that are due to be sent."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(FollowUp)
            .where(
                and_(
                    FollowUp.scheduled_at <= now,
                    FollowUp.sent_at.is_(None),
                    FollowUp.cancelled == False
                )
            )
            .order_by(FollowUp.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_sent(self, follow_up_id: UUID) -> FollowUp:
        """Mark follow-up as sent."""
        follow_up = await self.get_by_id(follow_up_id)
        if follow_up:
            follow_up.sent_at = datetime.utcnow()
            await self.session.flush()
        return follow_up

    async def mark_responded(
        self, follow_up_id: UUID, response_time: datetime
    ) -> FollowUp:
        """Mark that lead responded to follow-up."""
        follow_up = await self.get_by_id(follow_up_id)
        if follow_up:
            follow_up.lead_responded = True
            follow_up.response_at = response_time
            await self.session.flush()
        return follow_up

    async def cancel_pending_by_lead(self, lead_id: UUID) -> int:
        """Cancel all pending follow-ups for a lead."""
        pending = await self.get_pending_by_lead(lead_id)

        for follow_up in pending:
            follow_up.cancelled = True

        await self.session.flush()
        return len(pending)

    async def update(self, follow_up: FollowUp) -> FollowUp:
        """Update follow-up."""
        self.session.add(follow_up)
        await self.session.flush()
        return follow_up
