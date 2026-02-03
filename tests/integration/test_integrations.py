import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.mark.asyncio
async def test_llm_client_factory():
    """Test LLM client factory function."""
    from integrations.llm_client import get_llm_client, OpenAILLMClient, AnthropicLLMClient

    with patch.dict('os.environ', {'LLM_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-key'}):
        client = get_llm_client()
        assert isinstance(client, OpenAILLMClient)

    with patch.dict('os.environ', {'LLM_PROVIDER': 'anthropic', 'ANTHROPIC_API_KEY': 'test-key'}):
        client = get_llm_client()
        assert isinstance(client, AnthropicLLMClient)


@pytest.mark.asyncio
async def test_openai_client_has_methods():
    """Test OpenAI client has expected methods."""
    from integrations.llm_client import OpenAILLMClient

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LLM_TIMEOUT_SECONDS': '0.5'}):
        client = OpenAILLMClient()

        # Verify client has expected methods
        assert hasattr(client, 'generate_response')
        assert hasattr(client, 'detect_intent')
        assert client.model is not None


def test_whatsapp_client_factory():
    """Test WhatsApp client factory function."""
    from integrations.whatsapp_client import get_whatsapp_client, TwilioWhatsAppClient

    with patch.dict('os.environ', {
        'WHATSAPP_PROVIDER': 'twilio',
        'TWILIO_ACCOUNT_SID': 'test-sid',
        'TWILIO_AUTH_TOKEN': 'test-token',
        'TWILIO_WHATSAPP_NUMBER': '+1234567890'
    }):
        client = get_whatsapp_client()
        assert isinstance(client, TwilioWhatsAppClient)
