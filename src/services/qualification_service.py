from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lead import Lead
from src.repositories.lead_repository import LeadRepository
from src.services.intent_detector import IntentDetector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QualificationService:
    """Service for collecting and managing lead qualification data."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.lead_repo = LeadRepository(session)
        self.intent_detector = IntentDetector()

        # Required qualification fields (FR-004)
        self.required_fields = ["project_type", "budget", "timeline", "business_type"]

    async def process_message(
        self, lead: Lead, message: str, intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process message and extract qualification data.

        Args:
            lead: Lead instance
            message: User message
            intent: Detected intent

        Returns:
            Dict with extracted data and next action
        """
        extracted_data = {}
        next_question = None

        # Extract project type
        if not lead.project_type:
            project_type = self._extract_project_type(message)
            if project_type:
                extracted_data["project_type"] = project_type
                lead.project_type = project_type
                next_question = "budget"
            else:
                next_question = "project_type"

        # Extract budget (FR-005: ask within first 6 messages)
        elif not lead.budget:
            budget_data = self.intent_detector.extract_budget(message)
            if budget_data:
                extracted_data["budget"] = budget_data["budget"]
                extracted_data["budget_numeric"] = budget_data["budget_numeric"]
                lead.budget = budget_data["budget"]
                lead.budget_numeric = budget_data["budget_numeric"]
                next_question = "timeline"
            else:
                # Check for budget avoidance (FR-006)
                if self._is_budget_avoidance(message):
                    lead.budget_avoidance_count += 1
                    logger.info(
                        "Budget avoidance detected",
                        lead_id=str(lead.id),
                        count=lead.budget_avoidance_count,
                    )

                    if lead.budget_avoidance_count >= 2:
                        # Flag budget avoidance, move to next question
                        extracted_data["budget_avoidance_flagged"] = True
                        next_question = "timeline"
                    else:
                        next_question = "budget"
                else:
                    next_question = "budget"

        # Extract timeline
        elif not lead.timeline:
            timeline = self.intent_detector.extract_timeline(message)
            if timeline:
                extracted_data["timeline"] = timeline
                lead.timeline = timeline
                next_question = "business_type"
            else:
                next_question = "timeline"

        # Extract business type
        elif not lead.business_type:
            business_type = self._extract_business_type(message)
            if business_type:
                extracted_data["business_type"] = business_type
                lead.business_type = business_type
                next_question = None  # Qualification complete
            else:
                next_question = "business_type"

        # Update lead
        await self.lead_repo.update(lead)

        return {
            "extracted_data": extracted_data,
            "next_question": next_question,
            "is_complete": self.is_qualification_complete(lead),
        }

    def is_qualification_complete(self, lead: Lead) -> bool:
        """
        Check if all required qualification fields are collected.

        Args:
            lead: Lead instance

        Returns:
            True if qualification is complete
        """
        return all(
            [
                lead.project_type,
                lead.budget or lead.budget_avoidance_count >= 2,
                lead.timeline,
                lead.business_type,
            ]
        )

    def _extract_project_type(self, message: str) -> Optional[str]:
        """Extract project type from message."""
        message_lower = message.lower()

        project_types = {
            "website": ["website", "web site", "web app", "web application"],
            "mobile-app": ["mobile app", "mobile application", "ios app", "android app"],
            "e-commerce": ["e-commerce", "ecommerce", "online store", "shop"],
            "custom-software": ["custom software", "software", "system", "platform"],
        }

        for project_type, keywords in project_types.items():
            if any(keyword in message_lower for keyword in keywords):
                return project_type

        return None

    def _extract_business_type(self, message: str) -> Optional[str]:
        """Extract business type from message."""
        message_lower = message.lower()

        business_types = {
            "startup": ["startup", "start-up", "new business"],
            "enterprise": ["enterprise", "large company", "corporation"],
            "agency": ["agency", "consulting"],
            "small-business": ["small business", "smb"],
        }

        for business_type, keywords in business_types.items():
            if any(keyword in message_lower for keyword in keywords):
                return business_type

        return None

    def _is_budget_avoidance(self, message: str) -> bool:
        """Check if message indicates budget avoidance."""
        message_lower = message.lower()

        avoidance_phrases = [
            "not sure",
            "don't know",
            "later",
            "discuss later",
            "flexible",
            "depends",
            "varies",
        ]

        return any(phrase in message_lower for phrase in avoidance_phrases)

    def get_next_question_text(self, question_type: str) -> str:
        """Get question text for next qualification field."""
        questions = {
            "project_type": "What type of project are you looking to build?",
            "budget": "What's your budget range for this project?",
            "timeline": "When do you need this completed?",
            "business_type": "What type of business are you?",
        }

        return questions.get(question_type, "Can you tell me more about your needs?")
