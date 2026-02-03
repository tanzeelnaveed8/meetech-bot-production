from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lead import Lead
from src.models.conversation import Conversation
from src.models.enums import State, Sender, MessageType
from src.repositories.lead_repository import LeadRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.proof_asset_repository import ProofAssetRepository
from src.services.intent_detector import IntentDetector
from src.services.state_machine import StateMachine
from src.services.qualification_service import QualificationService
from src.services.response_generator import ResponseGenerator
from src.services.session_manager import SessionManager
from src.services.lead_scorer import LeadScorer
from src.services.handover_service import HandoverService
from src.services.follow_up_scheduler import FollowUpScheduler
from src.services.proof_asset_selector import ProofAssetSelector
from src.utils.state_logger import StateLogger
from src.utils.rate_limiter import check_rate_limit
from src.utils.content_filter import get_content_filter
from src.utils.logger import get_logger
from src.integrations.whatsapp_client import get_whatsapp_client

logger = get_logger(__name__)


class MessageProcessor:
    """Orchestrator for processing incoming WhatsApp messages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.lead_repo = LeadRepository(session)
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.proof_asset_repo = ProofAssetRepository(session)
        self.intent_detector = IntentDetector()
        self.state_machine = StateMachine()
        self.qualification_service = QualificationService(session)
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
        self.state_logger = StateLogger(session)
        self.content_filter = get_content_filter()
        self.whatsapp_client = get_whatsapp_client()
        self.lead_scorer = LeadScorer()
        self.handover_service = HandoverService(session)
        self.follow_up_scheduler = FollowUpScheduler(session)
        self.proof_asset_selector = ProofAssetSelector()

    async def process_message(
        self, phone_number: str, message_text: str, whatsapp_message_id: str
    ) -> Dict[str, Any]:
        """
        Process incoming WhatsApp message.

        Args:
            phone_number: Lead's phone number
            message_text: Message content
            whatsapp_message_id: WhatsApp message ID for deduplication

        Returns:
            Processing result with response
        """
        try:
            # Check rate limiting (constitution: 10 msg/min)
            if await check_rate_limit(phone_number):
                logger.warning("Rate limit exceeded", phone=phone_number)
                return {"status": "rate_limited"}

            # Check for duplicate message
            existing_message = await self.message_repo.get_by_whatsapp_id(
                whatsapp_message_id
            )
            if existing_message:
                logger.info("Duplicate message ignored", message_id=whatsapp_message_id)
                return {"status": "duplicate"}

            # Get or create lead
            lead = await self.lead_repo.get_by_phone(phone_number)
            if not lead:
                lead = await self.lead_repo.create(phone_number)
                logger.info("New lead created", lead_id=str(lead.id), phone=phone_number)

            # Get or create active conversation
            conversation = await self.conversation_repo.get_active_by_lead(lead.id)
            if not conversation:
                conversation = await self.conversation_repo.create(lead.id)
                logger.info(
                    "New conversation created", conversation_id=str(conversation.id)
                )

            # Check if human has taken over
            if not conversation.is_bot_active:
                logger.info(
                    "Human agent active, bot silent", conversation_id=str(conversation.id)
                )
                # Store message but don't respond
                await self.message_repo.create(
                    conversation.id,
                    Sender.LEAD,
                    message_text,
                    MessageType.TEXT,
                    whatsapp_message_id=whatsapp_message_id,
                )
                return {"status": "human_active"}

            # Detect intent
            intent_result = await self.intent_detector.detect_intent(message_text)
            logger.info(
                "Intent detected",
                intent=intent_result["intent"],
                confidence=intent_result["confidence"],
            )

            # Store incoming message
            await self.message_repo.create(
                conversation.id,
                Sender.LEAD,
                message_text,
                MessageType.TEXT,
                detected_intent=intent_result["intent"],
                intent_confidence=intent_result["confidence"],
                whatsapp_message_id=whatsapp_message_id,
            )

            # Cancel any pending follow-ups (lead responded)
            await self.follow_up_scheduler.cancel_pending_follow_ups(lead.id)

            # Check for pricing inquiry (constitution: defer to human)
            if self.intent_detector.is_pricing_inquiry(message_text):
                response_text = (
                    "Pricing is customized based on your specific needs. "
                    "Let me connect you with our team to discuss this in detail."
                )
                await self._send_response(conversation, lead, response_text)
                return {"status": "pricing_deferred", "response": response_text}

            # Process based on current state
            current_state = conversation.current_state
            response_text = await self._process_by_state(
                lead, conversation, message_text, intent_result
            )

            # Send response
            await self._send_response(conversation, lead, response_text)

            return {"status": "success", "response": response_text}

        except Exception as e:
            logger.error("Message processing failed", error=str(e), phone=phone_number)
            return {"status": "error", "error": str(e)}

    async def _process_by_state(
        self,
        lead: Lead,
        conversation: Conversation,
        message: str,
        intent: Dict[str, Any],
    ) -> str:
        """Process message based on current conversation state."""
        current_state = conversation.current_state

        if current_state == State.GREETING:
            # Transition to intent detection
            await self._transition_state(
                conversation, State.INTENT_DETECTION, "greeting_received"
            )
            return await self.response_generator.generate_greeting_response(lead)

        elif current_state == State.INTENT_DETECTION:
            # Transition to qualification
            await self._transition_state(
                conversation, State.QUALIFICATION, "intent_detected"
            )
            return await self.response_generator.generate_qualification_start(lead)

        elif current_state == State.QUALIFICATION:
            # Process qualification data
            result = await self.qualification_service.process_message(
                lead, message, intent
            )

            if result["is_complete"]:
                # Qualification complete, move to scoring
                await self._transition_state(
                    conversation, State.SCORING, "qualification_complete"
                )

                # Calculate lead score
                score_result = await self._calculate_and_handle_score(lead, conversation)

                return score_result["response"]
            else:
                # Ask next question
                next_question = result["next_question"]
                response = self.qualification_service.get_next_question_text(next_question)

                # Try to inject proof asset during qualification (US4)
                asset_message = await self._try_inject_proof_asset(lead, conversation)
                if asset_message:
                    response = f"{response}\n\n{asset_message}"

                return response

        elif current_state == State.SCORING:
            # Already scored, determine next action
            return "Thank you for the information. Our team will be in touch shortly."

        elif current_state == State.PROOF_DELIVERY:
            # Inject proof asset if not already done
            asset_message = await self._try_inject_proof_asset(lead, conversation)
            if asset_message:
                # Transition to call push after showing proof
                await self._transition_state(
                    conversation, State.CALL_PUSH, "proof_delivered"
                )
                return f"{asset_message}\n\nWould you like to schedule a call to discuss your project in detail?"
            else:
                # No relevant asset, skip to call push
                await self._transition_state(
                    conversation, State.CALL_PUSH, "no_proof_available"
                )
                return "Would you like to schedule a call to discuss your project in detail?"

        else:
            # Default response
            return "Thank you for your message. How can I help you today?"

    async def _transition_state(
        self, conversation: Conversation, new_state: State, trigger: str
    ) -> None:
        """Transition conversation to new state."""
        old_state = conversation.current_state

        # Validate transition
        self.state_machine.validate_transition(old_state, new_state)

        # Log transition
        await self.state_logger.log_transition(
            conversation.id, old_state, new_state, trigger
        )

        # Update conversation
        conversation.previous_state = old_state
        conversation.current_state = new_state
        await self.conversation_repo.update(conversation)

        logger.info(
            "State transition",
            conversation_id=str(conversation.id),
            from_state=old_state.value,
            to_state=new_state.value,
            trigger=trigger,
        )

    async def _send_response(
        self, conversation: Conversation, lead: Lead, response_text: str
    ) -> None:
        """Send response to lead via WhatsApp."""
        # Validate and sanitize response
        response_text = self.content_filter.enforce_brevity(response_text)
        response_text = self.content_filter.sanitize_response(response_text)

        # Store bot message
        await self.message_repo.create(
            conversation.id, Sender.BOT, response_text, MessageType.TEXT
        )

        # Send via WhatsApp
        await self.whatsapp_client.send_message(lead.phone_number, response_text)

        # Update conversation message count
        conversation.message_count += 1
        await self.conversation_repo.update(conversation)

    async def _calculate_and_handle_score(
        self, lead: Lead, conversation: Conversation
    ) -> Dict[str, Any]:
        """Calculate lead score and handle routing based on score."""
        # Prepare lead data for scoring
        lead_data = {
            "budget_numeric": lead.budget_numeric,
            "budget_avoidance_count": lead.budget_avoidance_count,
            "timeline": lead.timeline,
            "project_type": lead.project_type,
            "country": lead.country,
            "message_count": conversation.message_count,
            "response_pattern": "normal",  # TODO: Implement pattern detection
        }

        # Calculate score
        score_result = self.lead_scorer.calculate_total_score(lead_data)

        logger.info(
            "Lead scored",
            lead_id=str(lead.id),
            total_score=score_result["total_score"],
            category=score_result["score_category"].value
        )

        # Handle based on score category (FR-008, FR-009)
        if score_result["total_score"] >= 70:
            # High score - trigger human handover
            await self.handover_service.trigger_handover(
                conversation, lead, score_result, reason="high_score"
            )
            response = (
                "Thank you! Based on your requirements, I'd like to connect you "
                "with one of our senior team members who can discuss this in detail. "
                "They'll reach out to you shortly."
            )
        elif score_result["total_score"] >= 40:
            # Medium score - continue with proof delivery
            await self._transition_state(
                conversation, State.PROOF_DELIVERY, "medium_score"
            )
            response = (
                "Great! Let me share some relevant examples of our work. "
                "We've helped similar businesses achieve their goals."
            )
        else:
            # Low score - schedule follow-up
            await self._transition_state(
                conversation, State.FOLLOW_UP, "low_score"
            )

            # Schedule first follow-up (2 hours)
            from src.models.enums import FollowUpScenario
            await self.follow_up_scheduler.schedule_follow_up(
                lead.id,
                FollowUpScenario.INACTIVE,
                attempt=1
            )

            response = (
                "Thank you for your interest! We'll follow up with you soon "
                "with more information about how we can help."
            )

        return {"response": response, "score": score_result}

    async def _try_inject_proof_asset(
        self, lead: Lead, conversation: Conversation
    ) -> Optional[str]:
        """
        Try to inject a relevant proof asset into the conversation.

        Constitution requirement: Max 1 asset per conversation (US4)

        Args:
            lead: The lead
            conversation: The conversation

        Returns:
            Formatted asset message or None if no injection
        """
        # Check if injection is appropriate
        should_inject = self.proof_asset_selector.should_inject_asset(
            conversation_proof_asset_count=conversation.proof_asset_count,
            project_type=lead.project_type,
            current_state=conversation.current_state.value
        )

        if not should_inject:
            return None

        # Get available assets
        available_assets = await self.proof_asset_repo.list_active()

        if not available_assets:
            logger.info("No active proof assets available")
            return None

        # Select most relevant asset
        selected_asset = self.proof_asset_selector.select_asset(
            project_type=lead.project_type,
            available_assets=available_assets
        )

        if not selected_asset:
            logger.info(
                "No relevant proof asset found",
                project_type=lead.project_type
            )
            return None

        # Format asset message
        asset_message = self.proof_asset_selector.format_asset_message(selected_asset)

        # Update conversation proof asset count
        conversation.proof_asset_count += 1
        await self.conversation_repo.update(conversation)

        # Update asset usage tracking
        await self.proof_asset_repo.increment_usage(selected_asset.id)

        logger.info(
            "Proof asset injected",
            conversation_id=str(conversation.id),
            asset_id=str(selected_asset.id),
            asset_title=selected_asset.title
        )

        return asset_message
