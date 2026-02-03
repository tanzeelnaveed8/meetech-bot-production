"""
Metrics utility for Prometheus monitoring.

Tracks key performance indicators:
- Response time (constitution requirement: < 1 second p95)
- Message throughput
- Lead counts by state and score
- Error rates
- System health
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional
import time


# ============================================================================
# Response Time Metrics (Constitution: < 1 second p95)
# ============================================================================

response_time_histogram = Histogram(
    'bot_response_time_seconds',
    'Time taken to process and respond to messages',
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0]
)

# ============================================================================
# Message Metrics
# ============================================================================

messages_received_counter = Counter(
    'bot_messages_received_total',
    'Total number of messages received',
    ['sender_type']  # LEAD, BOT, HUMAN
)

messages_sent_counter = Counter(
    'bot_messages_sent_total',
    'Total number of messages sent',
    ['message_type']  # TEXT, IMAGE, etc.
)

messages_failed_counter = Counter(
    'bot_messages_failed_total',
    'Total number of failed message deliveries',
    ['error_type']
)

# ============================================================================
# Lead Metrics
# ============================================================================

leads_created_counter = Counter(
    'bot_leads_created_total',
    'Total number of leads created'
)

leads_by_state_gauge = Gauge(
    'bot_leads_by_state',
    'Current number of leads in each state',
    ['state']
)

leads_by_score_gauge = Gauge(
    'bot_leads_by_score_category',
    'Current number of leads in each score category',
    ['category']  # LOW, MEDIUM, HIGH
)

# ============================================================================
# Conversation Metrics
# ============================================================================

conversations_active_gauge = Gauge(
    'bot_conversations_active',
    'Number of currently active conversations'
)

conversations_created_counter = Counter(
    'bot_conversations_created_total',
    'Total number of conversations created'
)

conversations_ended_counter = Counter(
    'bot_conversations_ended_total',
    'Total number of conversations ended',
    ['end_reason']
)

# ============================================================================
# State Transition Metrics
# ============================================================================

state_transitions_counter = Counter(
    'bot_state_transitions_total',
    'Total number of state transitions',
    ['from_state', 'to_state']
)

# ============================================================================
# Scoring Metrics
# ============================================================================

lead_scores_histogram = Histogram(
    'bot_lead_scores',
    'Distribution of lead scores',
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# ============================================================================
# Human Handover Metrics
# ============================================================================

handovers_triggered_counter = Counter(
    'bot_handovers_triggered_total',
    'Total number of human handovers triggered',
    ['reason']  # high_score, pricing_inquiry, etc.
)

handovers_active_gauge = Gauge(
    'bot_handovers_active',
    'Number of conversations currently with human agents'
)

# ============================================================================
# Follow-up Metrics
# ============================================================================

followups_scheduled_counter = Counter(
    'bot_followups_scheduled_total',
    'Total number of follow-ups scheduled',
    ['scenario']  # INACTIVE, CALL_NOT_BOOKED, etc.
)

followups_sent_counter = Counter(
    'bot_followups_sent_total',
    'Total number of follow-ups sent',
    ['attempt']  # 1, 2, 3
)

followups_cancelled_counter = Counter(
    'bot_followups_cancelled_total',
    'Total number of follow-ups cancelled',
    ['reason']
)

# ============================================================================
# Proof Asset Metrics
# ============================================================================

proof_assets_injected_counter = Counter(
    'bot_proof_assets_injected_total',
    'Total number of proof assets injected',
    ['asset_type']  # PORTFOLIO, CASE_STUDY, TESTIMONIAL
)

# ============================================================================
# Error Metrics
# ============================================================================

errors_counter = Counter(
    'bot_errors_total',
    'Total number of errors',
    ['error_type', 'component']
)

# ============================================================================
# Rate Limiting Metrics
# ============================================================================

rate_limit_exceeded_counter = Counter(
    'bot_rate_limit_exceeded_total',
    'Total number of rate limit violations'
)

# ============================================================================
# System Health Metrics
# ============================================================================

bot_status_gauge = Gauge(
    'bot_status',
    'Bot status (1 = active, 0 = paused)'
)

database_connection_gauge = Gauge(
    'bot_database_connected',
    'Database connection status (1 = connected, 0 = disconnected)'
)

redis_connection_gauge = Gauge(
    'bot_redis_connected',
    'Redis connection status (1 = connected, 0 = disconnected)'
)


# ============================================================================
# Helper Functions
# ============================================================================

class ResponseTimeTracker:
    """Context manager for tracking response time."""

    def __init__(self):
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            response_time_histogram.observe(duration)


def track_response_time(func):
    """Decorator to track response time of async functions."""
    async def wrapper(*args, **kwargs):
        with ResponseTimeTracker():
            return await func(*args, **kwargs)
    return wrapper


def record_message_received(sender_type: str):
    """Record a received message."""
    messages_received_counter.labels(sender_type=sender_type).inc()


def record_message_sent(message_type: str):
    """Record a sent message."""
    messages_sent_counter.labels(message_type=message_type).inc()


def record_message_failed(error_type: str):
    """Record a failed message."""
    messages_failed_counter.labels(error_type=error_type).inc()


def record_lead_created():
    """Record a new lead creation."""
    leads_created_counter.inc()


def record_conversation_created():
    """Record a new conversation creation."""
    conversations_created_counter.inc()


def record_conversation_ended(end_reason: str):
    """Record a conversation ending."""
    conversations_ended_counter.labels(end_reason=end_reason).inc()


def record_state_transition(from_state: str, to_state: str):
    """Record a state transition."""
    state_transitions_counter.labels(
        from_state=from_state,
        to_state=to_state
    ).inc()


def record_lead_score(score: float):
    """Record a lead score."""
    lead_scores_histogram.observe(score)


def record_handover_triggered(reason: str):
    """Record a human handover."""
    handovers_triggered_counter.labels(reason=reason).inc()


def record_followup_scheduled(scenario: str):
    """Record a follow-up scheduled."""
    followups_scheduled_counter.labels(scenario=scenario).inc()


def record_followup_sent(attempt: int):
    """Record a follow-up sent."""
    followups_sent_counter.labels(attempt=str(attempt)).inc()


def record_followup_cancelled(reason: str):
    """Record a follow-up cancelled."""
    followups_cancelled_counter.labels(reason=reason).inc()


def record_proof_asset_injected(asset_type: str):
    """Record a proof asset injection."""
    proof_assets_injected_counter.labels(asset_type=asset_type).inc()


def record_error(error_type: str, component: str):
    """Record an error."""
    errors_counter.labels(error_type=error_type, component=component).inc()


def record_rate_limit_exceeded():
    """Record a rate limit violation."""
    rate_limit_exceeded_counter.inc()


def update_bot_status(is_active: bool):
    """Update bot status gauge."""
    bot_status_gauge.set(1 if is_active else 0)


def update_database_connection(is_connected: bool):
    """Update database connection status."""
    database_connection_gauge.set(1 if is_connected else 0)


def update_redis_connection(is_connected: bool):
    """Update Redis connection status."""
    redis_connection_gauge.set(1 if is_connected else 0)


def update_leads_by_state(state: str, count: int):
    """Update leads by state gauge."""
    leads_by_state_gauge.labels(state=state).set(count)


def update_leads_by_score(category: str, count: int):
    """Update leads by score category gauge."""
    leads_by_score_gauge.labels(category=category).set(count)


def update_active_conversations(count: int):
    """Update active conversations gauge."""
    conversations_active_gauge.set(count)


def update_active_handovers(count: int):
    """Update active handovers gauge."""
    handovers_active_gauge.set(count)


def get_metrics() -> bytes:
    """
    Get metrics in Prometheus format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """
    Get the content type for Prometheus metrics.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
