from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lead import Lead
from src.models.conversation import Conversation
from src.models.enums import State
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.human_agent_repository import HumanAgentRepository
from src.repositories.lead_score_repository import LeadScoreRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HandoverService:
    """Service for managing human agent handovers."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.agent_repo = HumanAgentRepository(session)
        self.score_repo = LeadScoreRepository(session)

    async def trigger_handover(
        self,
        conversation: Conversation,
        lead: Lead,
        score_data: Dict[str, Any],
        reason: str = "high_score"
    ) -> Dict[str, Any]:
        """
        Trigger human handover for high-scoring lead (FR-009).

        Args:
            conversation: Conversation instance
            lead: Lead instance
            score_data: Score calculation result
            reason: Reason for handover

        Returns:
            Handover result with agent assignment
        """
        try:
            # Create score record with handover flag
            lead_score = await self.score_repo.create(
                lead_id=lead.id,
                total_score=score_data["total_score"],
                budget_score=score_data["budget_score"],
                timeline_score=score_data["timeline_score"],
                clarity_score=score_data["clarity_score"],
                country_score=score_data["country_score"],
                behavior_score=score_data["behavior_score"],
                score_category=score_data["score_category"],
                reasoning=score_data["reasoning"],
                triggered_handover=True
            )

            # Transition conversation to HUMAN_HANDOVER state
            conversation.previous_state = conversation.current_state
            conversation.current_state = State.HUMAN_HANDOVER
            await self.conversation_repo.update(conversation)

            # Find available agent (optional - can be assigned later)
            available_agent = await self._find_available_agent()

            # Notify agents (implementation depends on notification system)
            await self._notify_agents(lead, conversation, score_data)

            logger.info(
                "Handover triggered",
                lead_id=str(lead.id),
                conversation_id=str(conversation.id),
                score=score_data["total_score"],
                reason=reason
            )

            return {
                "status": "handover_triggered",
                "lead_id": str(lead.id),
                "conversation_id": str(conversation.id),
                "score": score_data["total_score"],
                "available_agent": str(available_agent.id) if available_agent else None,
            }

        except Exception as e:
            logger.error("Handover trigger failed", error=str(e))
            raise

    async def assign_agent(
        self,
        conversation_id: UUID,
        agent_id: UUID
    ) -> Conversation:
        """
        Assign a human agent to a conversation.

        Args:
            conversation_id: Conversation ID
            agent_id: Agent ID

        Returns:
            Updated conversation
        """
        conversation = await self.conversation_repo.takeover(conversation_id, agent_id)

        logger.info(
            "Agent assigned",
            conversation_id=str(conversation_id),
            agent_id=str(agent_id)
        )

        return conversation

    async def get_handover_context(
        self,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Get full context for agent handover (FR-010).

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with conversation history, lead data, and score
        """
        from src.repositories.message_repository import MessageRepository
        from src.repositories.lead_repository import LeadRepository

        message_repo = MessageRepository(self.session)
        lead_repo = LeadRepository(self.session)

        # Get conversation
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get lead
        lead = await lead_repo.get_by_id(conversation.lead_id)

        # Get messages
        messages = await message_repo.list_by_conversation(conversation_id)

        # Get latest score
        latest_score = await self.score_repo.get_latest_by_lead(lead.id)

        return {
            "conversation": {
                "id": str(conversation.id),
                "started_at": conversation.started_at.isoformat(),
                "current_state": conversation.current_state.value,
                "message_count": conversation.message_count,
            },
            "lead": {
                "id": str(lead.id),
                "phone_number": lead.phone_number,
                "project_type": lead.project_type,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "business_type": lead.business_type,
                "country": lead.country,
            },
            "messages": [
                {
                    "sender": msg.sender.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent": msg.detected_intent,
                }
                for msg in messages
            ],
            "score": {
                "total": latest_score.total_score,
                "category": latest_score.score_category.value,
                "breakdown": {
                    "budget": latest_score.budget_score,
                    "timeline": latest_score.timeline_score,
                    "clarity": latest_score.clarity_score,
                    "country": latest_score.country_score,
                    "behavior": latest_score.behavior_score,
                },
                "reasoning": latest_score.reasoning,
            } if latest_score else None,
        }

    async def _find_available_agent(self):
        """Find an available agent with capacity."""
        agents = await self.agent_repo.list_available()

        # TODO: Implement load balancing logic
        # For now, return first available agent
        return agents[0] if agents else None

    async def _notify_agents(
        self,
        lead: Lead,
        conversation: Conversation,
        score_data: Dict[str, Any]
    ) -> None:
        """Notify agents of high-priority lead."""
        # TODO: Implement notification system
        # Could use:
        # - Slack webhook
        # - Email
        # - Push notification
        # - WebSocket to dashboard
        logger.info(
            "Agent notification sent",
            lead_id=str(lead.id),
            score=score_data["total_score"]
        )
