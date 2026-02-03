from typing import Dict, Any, Optional
import json
from src.db.redis_client import RedisClient
from src.models.lead import Lead
from src.models.conversation import Conversation


class SessionManager:
    """Manage conversation session state in Redis."""

    def __init__(self):
        self.redis = RedisClient()
        self.session_ttl = 3600  # 1 hour

    async def get_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get session data for a phone number."""
        await self.redis.connect()
        key = f"session:{phone_number}"
        data = await self.redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_session(
        self, phone_number: str, session_data: Dict[str, Any]
    ) -> None:
        """Set session data for a phone number."""
        await self.redis.connect()
        key = f"session:{phone_number}"
        data = json.dumps(session_data)
        await self.redis.set(key, data, ex=self.session_ttl)

    async def update_session(
        self, phone_number: str, updates: Dict[str, Any]
    ) -> None:
        """Update session data."""
        session = await self.get_session(phone_number)
        if session:
            session.update(updates)
            await self.set_session(phone_number, session)

    async def delete_session(self, phone_number: str) -> None:
        """Delete session data."""
        await self.redis.connect()
        key = f"session:{phone_number}"
        await self.redis.delete(key)

    async def store_conversation_context(
        self, phone_number: str, lead: Lead, conversation: Conversation
    ) -> None:
        """Store conversation context in session."""
        context = {
            "lead_id": str(lead.id),
            "conversation_id": str(conversation.id),
            "current_state": conversation.current_state.value,
            "project_type": lead.project_type,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "business_type": lead.business_type,
        }
        await self.set_session(phone_number, context)
