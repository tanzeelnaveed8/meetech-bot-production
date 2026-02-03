from typing import Dict, Any, Optional
import re
from src.integrations.llm_client import get_llm_client, LLMClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IntentDetector:
    """Service for detecting user intent from messages."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

        # Intent patterns for quick detection (fallback if LLM fails)
        self.patterns = {
            "greeting": [
                r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b",
            ],
            "project_inquiry": [
                r"\b(need|want|looking for|require)\b.*\b(website|app|mobile|platform|system)\b",
            ],
            "pricing_inquiry": [
                r"\b(price|cost|how much|pricing|quote|estimate)\b",
            ],
            "budget_question": [
                r"\b(budget|afford|spend|investment)\b",
            ],
            "timeline_question": [
                r"\b(when|timeline|deadline|how long|duration)\b",
            ],
        }

    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect intent from user message.

        Args:
            message: User message text

        Returns:
            Dict with intent, confidence, and optional extracted data
        """
        try:
            # Try LLM-based intent detection first
            result = await self._detect_with_llm(message)

            # Validate confidence threshold (constitution: 70%)
            if result["confidence"] >= 0.7:
                logger.info(
                    "Intent detected",
                    intent=result["intent"],
                    confidence=result["confidence"],
                )
                return result

            # If confidence too low, try pattern matching
            logger.warning(
                "Low confidence from LLM, trying pattern matching",
                confidence=result["confidence"],
            )
            return self._detect_with_patterns(message)

        except Exception as e:
            logger.error("Intent detection failed", error=str(e))
            # Fallback to pattern matching
            return self._detect_with_patterns(message)

    async def _detect_with_llm(self, message: str) -> Dict[str, Any]:
        """Detect intent using LLM."""
        system_prompt = """You are an intent classifier for a sales chatbot.
        Classify the user's message into one of these intents:
        - greeting: Initial hello/hi messages
        - project_inquiry: Asking about services or projects
        - budget_question: Discussing budget or pricing
        - timeline_question: Asking about project timeline
        - pricing_inquiry: Asking for specific prices (IMPORTANT: flag this)
        - general_question: Other questions

        Respond ONLY with JSON in this exact format:
        {"intent": "intent_name", "confidence": 0.95}

        Be strict: confidence should be 0.7+ only if you're certain."""

        response = await self.llm_client.generate_response(
            message, system_prompt, temperature=0.3, max_tokens=50
        )

        if not response.get("success"):
            return {"intent": "general_question", "confidence": 0.5}

        # Parse LLM response
        # TODO: Implement proper JSON parsing
        # For now, return mock response
        return {"intent": "general_question", "confidence": 0.8}

    def _detect_with_patterns(self, message: str) -> Dict[str, Any]:
        """Detect intent using regex patterns (fallback)."""
        message_lower = message.lower()

        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return {
                        "intent": intent,
                        "confidence": 0.85,  # Pattern matching is fairly reliable
                        "method": "pattern",
                    }

        # Default to general question
        return {"intent": "general_question", "confidence": 0.6, "method": "default"}

    def is_pricing_inquiry(self, message: str) -> bool:
        """
        Check if message is a pricing inquiry (constitution: must defer to human).

        Args:
            message: User message

        Returns:
            True if pricing inquiry detected
        """
        message_lower = message.lower()
        pricing_keywords = [
            "price",
            "cost",
            "how much",
            "pricing",
            "quote",
            "estimate",
            "payment",
            "pay",
        ]

        return any(keyword in message_lower for keyword in pricing_keywords)

    def extract_budget(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract budget information from message.

        Args:
            message: User message

        Returns:
            Dict with budget string and numeric value, or None
        """
        # Pattern for currency amounts
        patterns = [
            r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|thousand)?",  # $5000, $5k
            r"(\d+(?:,\d{3})*)\s*(?:dollars|usd|\$)",  # 5000 dollars
            r"(\d+)\s*-\s*(\d+)\s*(?:k|thousand)?",  # 5-10k range
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extract numeric value
                budget_str = match.group(0)
                # TODO: Implement proper budget parsing
                return {"budget": budget_str, "budget_numeric": 5000}

        return None

    def extract_timeline(self, message: str) -> Optional[str]:
        """
        Extract timeline information from message.

        Args:
            message: User message

        Returns:
            Timeline string or None
        """
        timeline_patterns = [
            r"(\d+)\s*(week|month|day)s?",
            r"(urgent|asap|immediately)",
            r"(flexible|no rush)",
        ]

        for pattern in timeline_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0)

        return None
