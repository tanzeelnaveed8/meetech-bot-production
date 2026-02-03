import pytest
from datetime import datetime


def test_state_enum():
    """Test State enum values."""
    from models.enums import State

    states = [
        State.GREETING,
        State.INTENT_DETECTION,
        State.QUALIFICATION,
        State.SCORING,
        State.PROOF_DELIVERY,
        State.CALL_PUSH,
        State.HUMAN_HANDOVER,
        State.FOLLOW_UP,
        State.EXIT,
        State.PARK,
    ]

    assert len(states) == 10
    assert State.GREETING.value == "GREETING"
    assert State.INTENT_DETECTION.value == "INTENT_DETECTION"
    assert State.EXIT.value == "EXIT"


def test_sender_enum():
    """Test Sender enum values."""
    from models.enums import Sender

    assert Sender.LEAD.value == "LEAD"
    assert Sender.BOT.value == "BOT"
    assert Sender.HUMAN.value == "HUMAN"


def test_message_type_enum():
    """Test MessageType enum values."""
    from models.enums import MessageType

    assert MessageType.TEXT.value == "TEXT"
    assert MessageType.IMAGE.value == "IMAGE"
    assert MessageType.DOCUMENT.value == "DOCUMENT"
    assert MessageType.VOICE.value == "VOICE"
    assert MessageType.BUTTON_REPLY.value == "BUTTON_REPLY"


def test_score_category_enum():
    """Test ScoreCategory enum values."""
    from models.enums import ScoreCategory

    assert ScoreCategory.LOW.value == "LOW"
    assert ScoreCategory.MEDIUM.value == "MEDIUM"
    assert ScoreCategory.HIGH.value == "HIGH"


def test_asset_type_enum():
    """Test AssetType enum values."""
    from models.enums import AssetType

    assert AssetType.PORTFOLIO.value == "PORTFOLIO"
    assert AssetType.CASE_STUDY.value == "CASE_STUDY"
    assert AssetType.TESTIMONIAL.value == "TESTIMONIAL"
