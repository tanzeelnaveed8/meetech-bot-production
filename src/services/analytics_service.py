from typing import Dict, Any, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.models.lead import Lead
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.lead_score import LeadScore
from src.models.enums import State, ScoreCategory


class AnalyticsService:
    """Service for aggregating analytics and metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics.

        Returns:
            Dictionary with analytics data
        """
        # Total counts
        total_leads = await self._get_total_leads()
        total_conversations = await self._get_total_conversations()
        total_messages = await self._get_total_messages()
        active_conversations = await self._get_active_conversations()

        # Performance metrics
        avg_response_time = await self._get_avg_response_time()

        # Lead distribution
        leads_by_score = await self._get_leads_by_score_category()
        leads_by_state = await self._get_leads_by_state()

        # Conversion metrics
        conversion_rate = await self._calculate_conversion_rate()

        # Top project types
        top_project_types = await self._get_top_project_types()

        return {
            "total_leads": total_leads,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "active_conversations": active_conversations,
            "avg_response_time_ms": avg_response_time,
            "leads_by_score_category": leads_by_score,
            "leads_by_state": leads_by_state,
            "conversion_rate": conversion_rate,
            "top_project_types": top_project_types
        }

    async def _get_total_leads(self) -> int:
        """Get total number of leads."""
        result = await self.session.execute(
            select(func.count(Lead.id))
        )
        return result.scalar() or 0

    async def _get_total_conversations(self) -> int:
        """Get total number of conversations."""
        result = await self.session.execute(
            select(func.count(Conversation.id))
        )
        return result.scalar() or 0

    async def _get_total_messages(self) -> int:
        """Get total number of messages."""
        result = await self.session.execute(
            select(func.count(Message.id))
        )
        return result.scalar() or 0

    async def _get_active_conversations(self) -> int:
        """Get number of active conversations (not ended)."""
        result = await self.session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.ended_at.is_(None)
            )
        )
        return result.scalar() or 0

    async def _get_avg_response_time(self) -> float:
        """
        Get average response time in milliseconds.

        Note: This is a placeholder. In production, this would be calculated
        from actual response time metrics stored in a time-series database.
        """
        # TODO: Implement actual response time tracking
        # For now, return a placeholder value
        return 850.0  # Placeholder: 850ms average

    async def _get_leads_by_score_category(self) -> Dict[str, int]:
        """Get lead count by score category."""
        result = await self.session.execute(
            select(
                LeadScore.score_category,
                func.count(LeadScore.id)
            ).group_by(LeadScore.score_category)
        )

        scores = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0
        }

        for category, count in result.all():
            if category:
                scores[category.value] = count

        return scores

    async def _get_leads_by_state(self) -> Dict[str, int]:
        """Get lead count by current state."""
        result = await self.session.execute(
            select(
                Lead.current_state,
                func.count(Lead.id)
            ).group_by(Lead.current_state)
        )

        states = {}
        for state, count in result.all():
            if state:
                states[state.value] = count

        return states

    async def _calculate_conversion_rate(self) -> float:
        """
        Calculate conversion rate (leads that reached HUMAN_HANDOVER or beyond).

        Returns:
            Conversion rate as percentage (0-100)
        """
        total_leads = await self._get_total_leads()

        if total_leads == 0:
            return 0.0

        # Count leads that reached human handover or beyond
        converted_states = [
            State.HUMAN_HANDOVER,
            State.CALL_PUSH,
            State.EXIT
        ]

        result = await self.session.execute(
            select(func.count(Lead.id)).where(
                Lead.current_state.in_(converted_states)
            )
        )

        converted_leads = result.scalar() or 0

        return round((converted_leads / total_leads) * 100, 2)

    async def _get_top_project_types(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top project types by lead count.

        Args:
            limit: Maximum number of project types to return

        Returns:
            List of project types with counts
        """
        result = await self.session.execute(
            select(
                Lead.project_type,
                func.count(Lead.id).label("count")
            )
            .where(Lead.project_type.isnot(None))
            .group_by(Lead.project_type)
            .order_by(func.count(Lead.id).desc())
            .limit(limit)
        )

        project_types = []
        for project_type, count in result.all():
            project_types.append({
                "project_type": project_type,
                "count": count
            })

        return project_types

    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            Performance metrics
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        # Messages in time period
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.created_at >= since
            )
        )
        messages_count = result.scalar() or 0

        # New leads in time period
        result = await self.session.execute(
            select(func.count(Lead.id)).where(
                Lead.created_at >= since
            )
        )
        new_leads = result.scalar() or 0

        # New conversations in time period
        result = await self.session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.started_at >= since
            )
        )
        new_conversations = result.scalar() or 0

        return {
            "time_period_hours": hours,
            "messages_count": messages_count,
            "new_leads": new_leads,
            "new_conversations": new_conversations,
            "messages_per_hour": round(messages_count / hours, 2) if hours > 0 else 0
        }
