from typing import Dict, Set, Optional
from src.models.enums import State


class StateMachine:
    """State machine for managing conversation flow."""

    def __init__(self):
        # Define valid state transitions
        self.transitions: Dict[State, Set[State]] = {
            State.GREETING: {State.INTENT_DETECTION, State.HUMAN_HANDOVER},
            State.INTENT_DETECTION: {State.QUALIFICATION, State.HUMAN_HANDOVER},
            State.QUALIFICATION: {State.SCORING, State.HUMAN_HANDOVER},
            State.SCORING: {
                State.PROOF_DELIVERY,
                State.CALL_PUSH,
                State.HUMAN_HANDOVER,
                State.FOLLOW_UP,
            },
            State.PROOF_DELIVERY: {State.CALL_PUSH, State.HUMAN_HANDOVER},
            State.CALL_PUSH: {State.HUMAN_HANDOVER, State.FOLLOW_UP, State.EXIT},
            State.HUMAN_HANDOVER: {State.FOLLOW_UP, State.EXIT},
            State.FOLLOW_UP: {State.QUALIFICATION, State.EXIT, State.PARK},
            State.EXIT: set(),  # Terminal state
            State.PARK: {State.FOLLOW_UP, State.EXIT},  # Inactive conversations
        }

    def can_transition(self, from_state: State, to_state: State) -> bool:
        """
        Check if transition from one state to another is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid, False otherwise
        """
        # Allow emergency human handover from any state
        if to_state == State.HUMAN_HANDOVER:
            return True

        # Check if transition is in allowed transitions
        return to_state in self.transitions.get(from_state, set())

    def get_next_state(
        self, current_state: State, trigger: str, context: Optional[Dict] = None
    ) -> State:
        """
        Determine next state based on current state and trigger.

        Args:
            current_state: Current conversation state
            trigger: What triggered the state change
            context: Additional context (e.g., lead score, intent)

        Returns:
            Next state
        """
        context = context or {}

        # State transition logic
        if current_state == State.GREETING:
            if trigger == "message_received":
                return State.INTENT_DETECTION

        elif current_state == State.INTENT_DETECTION:
            intent = context.get("intent")
            if intent in ["project_inquiry", "greeting", "general_question"]:
                return State.QUALIFICATION

        elif current_state == State.QUALIFICATION:
            # Check if all required fields are collected
            if self._is_qualification_complete(context):
                return State.SCORING

        elif current_state == State.SCORING:
            score = context.get("score", 0)
            if score >= 70:
                return State.HUMAN_HANDOVER
            elif score >= 40:
                return State.PROOF_DELIVERY
            else:
                return State.FOLLOW_UP

        elif current_state == State.PROOF_DELIVERY:
            return State.CALL_PUSH

        elif current_state == State.CALL_PUSH:
            if context.get("call_booked"):
                return State.HUMAN_HANDOVER
            else:
                return State.FOLLOW_UP

        # Default: stay in current state
        return current_state

    def _is_qualification_complete(self, context: Dict) -> bool:
        """Check if all required qualification fields are collected."""
        required_fields = ["project_type", "budget", "timeline", "business_type"]
        lead_data = context.get("lead_data", {})

        return all(lead_data.get(field) for field in required_fields)

    def get_allowed_transitions(self, current_state: State) -> Set[State]:
        """Get all allowed transitions from current state."""
        return self.transitions.get(current_state, set())

    def validate_transition(self, from_state: State, to_state: State) -> None:
        """
        Validate state transition and raise exception if invalid.

        Args:
            from_state: Current state
            to_state: Target state

        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition(from_state, to_state):
            raise ValueError(
                f"Invalid state transition: {from_state} -> {to_state}. "
                f"Allowed transitions: {self.get_allowed_transitions(from_state)}"
            )
