from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.state_transition import StateTransition
from src.models.enums import State


class StateLogger:
    """Utility for logging state machine transitions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_transition(
        self,
        conversation_id: UUID,
        from_state: State,
        to_state: State,
        trigger: str = None,
        metadata: dict = None
    ) -> StateTransition:
        """
        Log a state transition.

        Args:
            conversation_id: Conversation ID
            from_state: Previous state
            to_state: New state
            trigger: What triggered the transition
            metadata: Additional context

        Returns:
            Created StateTransition record
        """
        transition = StateTransition(
            conversation_id=conversation_id,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            metadata=metadata,
            transitioned_at=datetime.utcnow()
        )

        self.session.add(transition)
        await self.session.flush()

        return transition

    async def get_transition_history(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> list[StateTransition]:
        """Get transition history for a conversation."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(StateTransition)
            .where(StateTransition.conversation_id == conversation_id)
            .order_by(StateTransition.transitioned_at.asc())
            .limit(limit)
        )

        return list(result.scalars().all())
