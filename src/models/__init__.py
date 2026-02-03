from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models to ensure they're registered with Base
from src.models.lead import Lead
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.lead_score import LeadScore
from src.models.state_transition import StateTransition
from src.models.proof_asset import ProofAsset
from src.models.follow_up import FollowUp
from src.models.human_agent import HumanAgent

__all__ = [
    "Base",
    "Lead",
    "Conversation",
    "Message",
    "LeadScore",
    "StateTransition",
    "ProofAsset",
    "FollowUp",
    "HumanAgent",
]
