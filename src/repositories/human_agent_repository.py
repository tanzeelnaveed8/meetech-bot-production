from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.human_agent import HumanAgent


class HumanAgentRepository:
    """Repository for HumanAgent CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, email: str) -> HumanAgent:
        """Create a new human agent."""
        agent = HumanAgent(name=name, email=email)
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_by_id(self, agent_id: UUID) -> Optional[HumanAgent]:
        """Get agent by ID."""
        result = await self.session.execute(
            select(HumanAgent).where(HumanAgent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[HumanAgent]:
        """Get agent by email."""
        result = await self.session.execute(
            select(HumanAgent).where(HumanAgent.email == email)
        )
        return result.scalar_one_or_none()

    async def update(self, agent: HumanAgent) -> HumanAgent:
        """Update agent."""
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def list_available(self, limit: int = 100) -> List[HumanAgent]:
        """List available agents."""
        result = await self.session.execute(
            select(HumanAgent)
            .where(HumanAgent.is_available == True)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100) -> List[HumanAgent]:
        """List all agents."""
        result = await self.session.execute(
            select(HumanAgent).limit(limit)
        )
        return list(result.scalars().all())

    async def set_availability(self, agent_id: UUID, is_available: bool) -> HumanAgent:
        """Set agent availability status."""
        agent = await self.get_by_id(agent_id)
        if agent:
            agent.is_available = is_available
            await self.session.flush()
        return agent

    async def update_last_active(self, agent_id: UUID) -> HumanAgent:
        """Update agent's last active timestamp."""
        from datetime import datetime
        agent = await self.get_by_id(agent_id)
        if agent:
            agent.last_active_at = datetime.utcnow()
            await self.session.flush()
        return agent
