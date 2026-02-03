from fastapi import APIRouter, Request, HTTPException, Query
from typing import Dict, Any
import hmac
import hashlib
import os
from dotenv import load_dotenv

from src.services.message_processor import MessageProcessor
from src.db.connection import get_db_session
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

router = APIRouter()

WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET", "")


@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """
    Webhook verification endpoint (GET).
    Called by WhatsApp during setup to verify the webhook.
    """
    logger.info("Webhook verification requested", mode=hub_mode)

    if hub_mode == "subscribe" and hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return hub_challenge
    else:
        logger.warning("Webhook verification failed", token_match=False)
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    """
    Webhook message receiver endpoint (POST).
    Receives WhatsApp messages and processes them.

    Constitution requirement: Must respond within 1 second.
    """
    try:
        # Get request body
        body = await request.body()
        payload = await request.json()

        # Verify webhook signature (security)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Extract message data
        message_data = extract_message_data(payload)
        if not message_data:
            logger.info("No message data in webhook")
            return {"status": "no_message"}

        # Process message
        async with get_db_session() as session:
            processor = MessageProcessor(session)
            result = await processor.process_message(
                phone_number=message_data["phone"],
                message_text=message_data["message"],
                whatsapp_message_id=message_data["message_id"],
            )

        logger.info("Message processed", result=result["status"])

        return {"status": "received", "message_id": message_data["message_id"]}

    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "error": str(e)}


def verify_signature(payload: bytes, signature: str) -> bool:
    """
    Verify WhatsApp webhook signature.

    Args:
        payload: Request body bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured, skipping verification")
        return True  # Skip verification in development

    try:
        # Calculate expected signature
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Compare signatures
        provided_signature = signature.replace("sha256=", "")
        return hmac.compare_digest(expected_signature, provided_signature)

    except Exception as e:
        logger.error("Signature verification error", error=str(e))
        return False


def extract_message_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract message data from WhatsApp webhook payload.

    Args:
        payload: Webhook payload

    Returns:
        Dict with phone, message, and message_id
    """
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        message = messages[0]

        return {
            "phone": message.get("from"),
            "message": message.get("text", {}).get("body", ""),
            "message_id": message.get("id"),
            "message_type": message.get("type"),
        }

    except (IndexError, KeyError) as e:
        logger.error("Failed to extract message data", error=str(e))
        return None
