from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


class LLMClient(ABC):
    """Abstract LLM client interface."""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect intent from a message."""
        pass


class OpenAILLMClient(LLMClient):
    """OpenAI LLM client implementation using LangChain."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=self.api_key,
            request_timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "0.5")),
        )

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self.model.agenerate([messages])
            content = response.generations[0][0].text
            return {
                "response": content,
                "model": "gpt-4",
                "success": True,
            }
        except Exception as e:
            return {
                "response": "I apologize, but I'm having trouble processing your message. Let me connect you with a human agent.",
                "model": "gpt-4",
                "success": False,
                "error": str(e),
            }

    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect intent from a message using OpenAI."""
        system_prompt = """You are an intent classifier for a sales chatbot.
        Classify the user's message into one of these intents:
        - greeting: Initial hello/hi messages
        - project_inquiry: Asking about services or projects
        - budget_question: Discussing budget or pricing
        - timeline_question: Asking about project timeline
        - pricing_inquiry: Asking for specific prices
        - general_question: Other questions

        Respond with JSON: {"intent": "intent_name", "confidence": 0.0-1.0}"""

        response = await self.generate_response(message, system_prompt, temperature=0.3)

        # TODO: Parse JSON response properly
        return {
            "intent": "general_question",
            "confidence": 0.8,
        }


class AnthropicLLMClient(LLMClient):
    """Anthropic Claude LLM client implementation using LangChain."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            anthropic_api_key=self.api_key,
            timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "0.5")),
        )

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> Dict[str, Any]:
        """Generate a response using Anthropic Claude."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self.model.agenerate([messages])
            content = response.generations[0][0].text
            return {
                "response": content,
                "model": "claude-3-sonnet",
                "success": True,
            }
        except Exception as e:
            return {
                "response": "I apologize, but I'm having trouble processing your message. Let me connect you with a human agent.",
                "model": "claude-3-sonnet",
                "success": False,
                "error": str(e),
            }

    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect intent from a message using Claude."""
        system_prompt = """You are an intent classifier for a sales chatbot.
        Classify the user's message into one of these intents:
        - greeting: Initial hello/hi messages
        - project_inquiry: Asking about services or projects
        - budget_question: Discussing budget or pricing
        - timeline_question: Asking about project timeline
        - pricing_inquiry: Asking for specific prices
        - general_question: Other questions

        Respond with JSON: {"intent": "intent_name", "confidence": 0.0-1.0}"""

        response = await self.generate_response(message, system_prompt, temperature=0.3)

        # TODO: Parse JSON response properly
        return {
            "intent": "general_question",
            "confidence": 0.8,
        }


def get_llm_client() -> LLMClient:
    """Factory function to get LLM client based on provider."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAILLMClient()
    elif provider == "anthropic":
        return AnthropicLLMClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
