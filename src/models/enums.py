from enum import Enum


class State(str, Enum):
    """Conversation state machine states."""
    GREETING = "GREETING"
    INTENT_DETECTION = "INTENT_DETECTION"
    QUALIFICATION = "QUALIFICATION"
    SCORING = "SCORING"
    PROOF_DELIVERY = "PROOF_DELIVERY"
    CALL_PUSH = "CALL_PUSH"
    HUMAN_HANDOVER = "HUMAN_HANDOVER"
    FOLLOW_UP = "FOLLOW_UP"
    EXIT = "EXIT"
    PARK = "PARK"


class Sender(str, Enum):
    """Message sender type."""
    LEAD = "LEAD"
    BOT = "BOT"
    HUMAN = "HUMAN"


class MessageType(str, Enum):
    """Type of message content."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VOICE = "VOICE"
    DOCUMENT = "DOCUMENT"
    BUTTON_REPLY = "BUTTON_REPLY"


class ScoreCategory(str, Enum):
    """Lead score category."""
    LOW = "LOW"        # 0-39
    MEDIUM = "MEDIUM"  # 40-69
    HIGH = "HIGH"      # 70+


class AssetType(str, Enum):
    """Proof asset type."""
    PORTFOLIO = "PORTFOLIO"
    CASE_STUDY = "CASE_STUDY"
    TESTIMONIAL = "TESTIMONIAL"


class FollowUpScenario(str, Enum):
    """Follow-up trigger scenario."""
    INACTIVE = "INACTIVE"
    CALL_NOT_BOOKED = "CALL_NOT_BOOKED"
    CALL_MISSED = "CALL_MISSED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
