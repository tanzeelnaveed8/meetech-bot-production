from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.follow_up import FollowUp
from src.models.lead import Lead
from src.models.enums import FollowUpScenario
from src.repositories.follow_up_repository import FollowUpRepository
from src.repositories.lead_repository import LeadRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FollowUpScheduler:
    """Service for scheduling and managing automated follow-ups."""

    # Follow-up intervals per constitution (FR-013)
    INTERVALS = {
        1: timedelta(hours=2),
        2: timedelta(hours=24),
        3: timedelta(days=3),
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.follow_up_repo = FollowUpRepository(session)
        self.lead_repo = LeadRepository(session)

    @staticmethod
    def get_follow_up_intervals() -> List[timedelta]:
        """Get follow-up intervals."""
        return [
            FollowUpScheduler.INTERVALS[1],
            FollowUpScheduler.INTERVALS[2],
            FollowUpScheduler.INTERVALS[3],
        ]

    @staticmethod
    def is_inactive(last_message_time: datetime) -> bool:
        """
        Check if lead is inactive (no response for 2+ hours).

        Args:
            last_message_time: Timestamp of last message

        Returns:
            True if inactive
        """
        time_since_last_message = datetime.utcnow() - last_message_time
        return time_since_last_message >= timedelta(hours=2)

    @staticmethod
    def calculate_scheduled_time(base_time: datetime, attempt: int) -> datetime:
        """
        Calculate scheduled time for follow-up attempt.

        Args:
            base_time: Base timestamp
            attempt: Attempt number (1, 2, or 3)

        Returns:
            Scheduled datetime
        """
        if attempt not in FollowUpScheduler.INTERVALS:
            raise ValueError(f"Invalid attempt number: {attempt}. Must be 1, 2, or 3.")

        return base_time + FollowUpScheduler.INTERVALS[attempt]

    @staticmethod
    def get_follow_up_message(scenario: FollowUpScenario, attempt: int) -> str:
        """
        Get follow-up message template for scenario and attempt.

        Args:
            scenario: Follow-up scenario
            attempt: Attempt number (1, 2, or 3)

        Returns:
            Follow-up message text
        """
        messages = {
            FollowUpScenario.INACTIVE: {
                1: "Hi! Just checking in. Are you still interested in discussing your project?",
                2: "Hello! I wanted to follow up on your project inquiry. Let me know if you'd like to continue our conversation.",
                3: "This is my last follow-up. If you're still interested in your project, feel free to reach out anytime!",
            },
            FollowUpScenario.CALL_NOT_BOOKED: {
                1: "Hi! I noticed you haven't booked a call yet. Would you like to schedule a time to discuss your project?",
                2: "Just following up on scheduling a call. Our team is ready to discuss your project whenever you're available.",
                3: "Last reminder about scheduling a call. Let us know if you'd like to connect with our team!",
            },
            FollowUpScenario.CALL_MISSED: {
                1: "Hi! We missed you on our scheduled call. Would you like to reschedule?",
                2: "Following up on our missed call. We're happy to find another time that works for you.",
                3: "Final follow-up about rescheduling. Let us know if you'd still like to connect!",
            },
            FollowUpScenario.PROPOSAL_SENT: {
                1: "Hi! Just checking if you had a chance to review the proposal we sent?",
                2: "Following up on the proposal. Do you have any questions or need clarification on anything?",
                3: "Last follow-up on our proposal. We're here if you need any additional information!",
            },
        }

        return messages.get(scenario, {}).get(attempt, "Following up on your inquiry.")

    async def schedule_follow_up(
        self,
        lead_id: UUID,
        scenario: FollowUpScenario,
        attempt: int = 1
    ) -> FollowUp:
        """
        Schedule a follow-up for a lead.

        Args:
            lead_id: Lead ID
            scenario: Follow-up scenario
            attempt: Attempt number (1, 2, or 3)

        Returns:
            Created FollowUp record
        """
        # Validate attempt number (FR-014: max 3 attempts)
        if attempt > 3:
            logger.warning(
                "Attempt to schedule more than 3 follow-ups",
                lead_id=str(lead_id),
                attempt=attempt
            )
            raise ValueError("Maximum 3 follow-up attempts allowed")

        # Calculate scheduled time
        scheduled_at = self.calculate_scheduled_time(datetime.utcnow(), attempt)

        # Get message template
        message_content = self.get_follow_up_message(scenario, attempt)

        # Create follow-up record
        follow_up = await self.follow_up_repo.create(
            lead_id=lead_id,
            trigger_scenario=scenario,
            attempt_number=attempt,
            scheduled_at=scheduled_at,
            message_content=message_content
        )

        logger.info(
            "Follow-up scheduled",
            lead_id=str(lead_id),
            scenario=scenario.value,
            attempt=attempt,
            scheduled_at=scheduled_at.isoformat()
        )

        return follow_up

    async def cancel_pending_follow_ups(self, lead_id: UUID) -> int:
        """
        Cancel all pending follow-ups for a lead (when they respond).

        Args:
            lead_id: Lead ID

        Returns:
            Number of follow-ups cancelled
        """
        cancelled_count = await self.follow_up_repo.cancel_pending_by_lead(lead_id)

        logger.info(
            "Follow-ups cancelled",
            lead_id=str(lead_id),
            count=cancelled_count
        )

        return cancelled_count

    async def mark_follow_up_sent(self, follow_up_id: UUID) -> FollowUp:
        """
        Mark follow-up as sent.

        Args:
            follow_up_id: FollowUp ID

        Returns:
            Updated FollowUp record
        """
        follow_up = await self.follow_up_repo.mark_sent(follow_up_id)

        logger.info("Follow-up marked as sent", follow_up_id=str(follow_up_id))

        return follow_up

    async def mark_lead_responded(
        self, follow_up_id: UUID, response_time: datetime
    ) -> FollowUp:
        """
        Mark that lead responded to follow-up.

        Args:
            follow_up_id: FollowUp ID
            response_time: When lead responded

        Returns:
            Updated FollowUp record
        """
        follow_up = await self.follow_up_repo.mark_responded(
            follow_up_id, response_time
        )

        logger.info(
            "Lead responded to follow-up",
            follow_up_id=str(follow_up_id),
            response_time=response_time.isoformat()
        )

        return follow_up

    async def get_due_follow_ups(self) -> List[FollowUp]:
        """
        Get follow-ups that are due to be sent.

        Returns:
            List of due follow-ups
        """
        return await self.follow_up_repo.get_due_follow_ups()

    async def schedule_next_attempt(self, follow_up: FollowUp) -> Optional[FollowUp]:
        """
        Schedule next follow-up attempt if not at max.

        Args:
            follow_up: Current follow-up

        Returns:
            Next follow-up or None if at max attempts
        """
        if follow_up.attempt_number >= 3:
            logger.info(
                "Max follow-up attempts reached",
                lead_id=str(follow_up.lead_id)
            )
            return None

        next_attempt = follow_up.attempt_number + 1
        return await self.schedule_follow_up(
            follow_up.lead_id,
            follow_up.trigger_scenario,
            next_attempt
        )
