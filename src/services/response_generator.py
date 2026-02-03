from typing import Optional
from src.models.lead import Lead
from src.integrations.llm_client import get_llm_client, LLMClient
from src.utils.content_filter import get_content_filter


class ResponseGenerator:
    """Generate bot responses using LLM and templates."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.content_filter = get_content_filter()

    async def generate_greeting_response(self, lead: Lead) -> str:
        """Generate greeting response."""
        # Use template for consistency
        return (
            "Hi! Thanks for reaching out. "
            "I'm here to help you with your project. What are you looking to build?"
        )

    async def generate_qualification_start(self, lead: Lead) -> str:
        """Generate response to start qualification."""
        return "Great! Let me ask you a few quick questions to understand your needs better. What type of project are you looking to build?"

    async def generate_response(
        self, prompt: str, context: Optional[dict] = None
    ) -> str:
        """
        Generate response using LLM.

        Args:
            prompt: User message
            context: Conversation context

        Returns:
            Generated response
        """
        system_prompt = """You are a friendly sales assistant for a software development company.
        Your role is to qualify leads by asking about their project needs.

        Guidelines:
        - Keep responses SHORT (1-3 sentences, max 300 characters)
        - Be conversational and friendly
        - Never commit to specific prices
        - Ask one question at a time
        - Be confident and professional"""

        response = await self.llm_client.generate_response(
            prompt, system_prompt, temperature=0.7, max_tokens=100
        )

        if response.get("success"):
            text = response["response"]
            # Enforce brevity and brand safety
            text = self.content_filter.enforce_brevity(text)
            text = self.content_filter.sanitize_response(text)
            return text
        else:
            # Fallback response
            return "Thanks for your message. Can you tell me more about what you're looking for?"

    async def generate_pricing_deferral(self) -> str:
        """Generate response for pricing inquiries (constitution requirement)."""
        return (
            "Pricing is customized based on your specific needs and requirements. "
            "Let me connect you with our team to discuss this in detail."
        )

    async def generate_budget_question(self, attempt: int = 1) -> str:
        """Generate budget question (FR-005: ask within first 6 messages)."""
        if attempt == 1:
            return "What's your budget range for this project?"
        elif attempt == 2:
            return "Having a budget range helps us recommend the best solution. What are you looking to invest?"
        else:
            # After 2 attempts, move on (FR-006)
            return "No problem, we can discuss budget details later. When do you need this completed?"
