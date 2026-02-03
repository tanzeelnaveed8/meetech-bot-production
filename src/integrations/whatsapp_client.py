from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class WhatsAppClient(ABC):
    """Abstract WhatsApp client interface."""

    @abstractmethod
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message."""
        pass

    @abstractmethod
    async def send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send an image message."""
        pass

    @abstractmethod
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        pass


class TwilioWhatsAppClient(WhatsAppClient):
    """Twilio WhatsApp client implementation."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message via Twilio."""
        # TODO: Implement Twilio API call
        return {"status": "sent", "message_id": "mock_id"}

    async def send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send an image message via Twilio."""
        # TODO: Implement Twilio API call
        return {"status": "sent", "message_id": "mock_id"}

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Twilio webhook signature."""
        # TODO: Implement signature verification
        return True


class MetaWhatsAppClient(WhatsAppClient):
    """Meta (Facebook) WhatsApp client implementation."""

    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message via Meta API."""
        # TODO: Implement Meta API call
        return {"status": "sent", "message_id": "mock_id"}

    async def send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send an image message via Meta API."""
        # TODO: Implement Meta API call
        return {"status": "sent", "message_id": "mock_id"}

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Meta webhook signature."""
        # TODO: Implement signature verification
        return True


def get_whatsapp_client() -> WhatsAppClient:
    """Factory function to get WhatsApp client based on provider."""
    provider = os.getenv("WHATSAPP_PROVIDER", "meta").lower()

    if provider == "twilio":
        return TwilioWhatsAppClient()
    elif provider == "meta":
        return MetaWhatsAppClient()
    else:
        raise ValueError(f"Unsupported WhatsApp provider: {provider}")
