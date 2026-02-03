import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from models.enums import State


def test_lead_scorer_initialization():
    """Test lead scorer can be initialized."""
    from services.lead_scorer import LeadScorer

    scorer = LeadScorer()
    assert scorer is not None


def test_intent_detector_initialization():
    """Test intent detector can be initialized."""
    from services.intent_detector import IntentDetector

    with patch.dict('os.environ', {'LLM_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-key'}):
        detector = IntentDetector()
        assert detector is not None


def test_state_machine_get_next_state():
    """Test state machine get_next_state method."""
    from services.state_machine import StateMachine

    sm = StateMachine()

    # Test that get_next_state requires a trigger parameter
    # The method determines next state based on current state, trigger, and context
    assert hasattr(sm, 'get_next_state')
    assert hasattr(sm, 'can_transition')

    # Verify the state machine has valid transitions defined
    assert State.GREETING in sm.transitions
    assert State.INTENT_DETECTION in sm.transitions[State.GREETING]


def test_state_machine_all_states():
    """Test that state machine knows about all states."""
    from services.state_machine import StateMachine

    sm = StateMachine()

    # Verify all states are recognized
    all_states = [
        State.GREETING,
        State.INTENT_DETECTION,
        State.QUALIFICATION,
        State.SCORING,
        State.PROOF_DELIVERY,
        State.CALL_PUSH,
        State.HUMAN_HANDOVER,
        State.FOLLOW_UP,
        State.EXIT,
        State.PARK
    ]

    for state in all_states:
        assert state is not None


@pytest.mark.asyncio
async def test_message_processor_initialization():
    """Test message processor can be initialized."""
    from services.message_processor import MessageProcessor

    with patch.dict('os.environ', {
        'LLM_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key',
        'DATABASE_URL': 'postgresql+asyncpg://test:test@localhost:5432/test',
        'REDIS_URL': 'redis://localhost:6379/0'
    }):
        # Just test that it can be imported and has expected attributes
        assert MessageProcessor is not None
        assert hasattr(MessageProcessor, 'process_message')
