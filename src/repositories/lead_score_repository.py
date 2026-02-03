from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.lead_score import LeadScore
from src.models.enums import ScoreCategory


class LeadScoreRepository:
    """Repository for LeadScore CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        lead_id: UUID,
        total_score: int,
        budget_score: int,
        timeline_score: int,
        clarity_score: int,
        country_score: int,
        behavior_score: int,
        score_category: ScoreCategory,
        reasoning: str,
        triggered_handover: bool = False
    ) -> LeadScore:
        """Create a new lead score record."""
        lead_score = LeadScore(
            lead_id=lead_id,
            total_score=total_score,
            budget_score=budget_score,
            timeline_score=timeline_score,
            clarity_score=clarity_score,
            country_score=country_score,
            behavior_score=behavior_score,
            score_category=score_category,
            reasoning=reasoning,
            triggered_handover=triggered_handover
        )
        self.session.add(lead_score)
        await self.session.flush()
        return lead_score

    async def get_by_id(self, score_id: UUID) -> Optional[LeadScore]:
        """Get lead score by ID."""
        result = await self.session.execute(
            select(LeadScore).where(LeadScore.id == score_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_by_lead(self, lead_id: UUID) -> Optional[LeadScore]:
        """Get latest score for a lead."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.lead_id == lead_id)
            .order_by(LeadScore.calculated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_lead(self, lead_id: UUID) -> List[LeadScore]:
        """List all scores for a lead (score history)."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.lead_id == lead_id)
            .order_by(LeadScore.calculated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_category(
        self, category: ScoreCategory, limit: int = 100
    ) -> List[LeadScore]:
        """List scores by category."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.score_category == category)
            .order_by(LeadScore.calculated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_high_scores_pending_handover(self, limit: int = 50) -> List[LeadScore]:
        """List high-scoring leads that triggered handover."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.score_category == ScoreCategory.HIGH)
            .where(LeadScore.triggered_handover == True)
            .order_by(LeadScore.calculated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
