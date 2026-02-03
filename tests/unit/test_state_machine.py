import pytest
from models.enums import State


def test_state_machine_import():
    """Test that StateMachine can be imported."""
    from services.state_machine import StateMachine
    assert StateMachine is not None


def test_state_transitions():
    """Test valid state transitions."""
    from services.state_machine import StateMachine

    sm = StateMachine()

    # Test greeting to intent detection
    assert sm.can_transition(State.GREETING, State.INTENT_DETECTION)

    # Test intent detection to qualification
    assert sm.can_transition(State.INTENT_DETECTION, State.QUALIFICATION)

    # Test qualification to scoring
    assert sm.can_transition(State.QUALIFICATION, State.SCORING)


def test_invalid_state_transitions():
    """Test invalid state transitions."""
    from services.state_machine import StateMachine

    sm = StateMachine()

    # Cannot go from greeting directly to scoring
    assert not sm.can_transition(State.GREETING, State.SCORING)

    # Cannot go from exit back to greeting
    assert not sm.can_transition(State.EXIT, State.GREETING)
