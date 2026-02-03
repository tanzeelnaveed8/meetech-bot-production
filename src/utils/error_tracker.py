"""
Error tracking integration with Sentry.

Provides:
- Automatic error capture and reporting
- Performance monitoring
- Release tracking
- User context for debugging
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from typing import Optional, Dict, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> None:
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)
    """
    dsn = dsn or os.getenv("SENTRY_DSN")

    if not dsn:
        logger.warning("Sentry DSN not configured, error tracking disabled")
        return

    environment = environment or os.getenv("ENVIRONMENT", "development")
    release = release or os.getenv("RELEASE_VERSION", "1.0.0")

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration()
            ],
            # Send default PII (Personally Identifiable Information)
            send_default_pii=False,
            # Attach stack traces to messages
            attach_stacktrace=True,
            # Maximum breadcrumbs
            max_breadcrumbs=50,
            # Before send callback for filtering
            before_send=before_send_filter,
        )

        logger.info(
            "Sentry initialized",
            environment=environment,
            release=release
        )

    except Exception as e:
        logger.error("Failed to initialize Sentry", error=str(e))


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter events before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop the event
    """
    # Filter out specific errors
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Don't send rate limit errors
        if "rate_limit" in str(exc_value).lower():
            return None

        # Don't send validation errors
        if "validation" in str(exc_value).lower():
            return None

    # Scrub sensitive data
    if "request" in event:
        request = event["request"]

        # Remove sensitive headers
        if "headers" in request:
            sensitive_headers = ["authorization", "x-api-key", "cookie"]
            for header in sensitive_headers:
                if header in request["headers"]:
                    request["headers"][header] = "[REDACTED]"

        # Remove sensitive query params
        if "query_string" in request:
            sensitive_params = ["token", "api_key", "password"]
            for param in sensitive_params:
                if param in request["query_string"]:
                    request["query_string"] = request["query_string"].replace(
                        param, "[REDACTED]"
                    )

    return event


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        error: Exception to capture
        context: Additional context
        level: Error level (error, warning, info)

    Returns:
        Event ID or None
    """
    try:
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level

            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)

            # Capture exception
            event_id = sentry_sdk.capture_exception(error)

            logger.info(
                "Exception captured by Sentry",
                event_id=event_id,
                error_type=type(error).__name__
            )

            return event_id

    except Exception as e:
        logger.error("Failed to capture exception in Sentry", error=str(e))
        return None


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Capture a message and send to Sentry.

    Args:
        message: Message to capture
        level: Message level (error, warning, info)
        context: Additional context

    Returns:
        Event ID or None
    """
    try:
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level

            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)

            # Capture message
            event_id = sentry_sdk.capture_message(message)

            return event_id

    except Exception as e:
        logger.error("Failed to capture message in Sentry", error=str(e))
        return None


def set_user_context(
    user_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    **kwargs
) -> None:
    """
    Set user context for error tracking.

    Args:
        user_id: User/Lead ID
        phone_number: Phone number (will be hashed for privacy)
        email: Email address (will be hashed for privacy)
        **kwargs: Additional user attributes
    """
    try:
        import hashlib

        user_data = {}

        if user_id:
            user_data["id"] = user_id

        # Hash PII for privacy
        if phone_number:
            user_data["phone_hash"] = hashlib.sha256(
                phone_number.encode()
            ).hexdigest()[:16]

        if email:
            user_data["email_hash"] = hashlib.sha256(
                email.encode()
            ).hexdigest()[:16]

        # Add additional attributes
        user_data.update(kwargs)

        sentry_sdk.set_user(user_data)

    except Exception as e:
        logger.error("Failed to set user context in Sentry", error=str(e))


def set_tag(key: str, value: str) -> None:
    """
    Set a tag for error tracking.

    Args:
        key: Tag key
        value: Tag value
    """
    try:
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error("Failed to set tag in Sentry", error=str(e))


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add a breadcrumb for error tracking.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level
        data: Additional data
    """
    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except Exception as e:
        logger.error("Failed to add breadcrumb in Sentry", error=str(e))


def start_transaction(
    name: str,
    op: str = "task"
) -> Any:
    """
    Start a performance transaction.

    Args:
        name: Transaction name
        op: Operation type

    Returns:
        Transaction object
    """
    try:
        return sentry_sdk.start_transaction(name=name, op=op)
    except Exception as e:
        logger.error("Failed to start transaction in Sentry", error=str(e))
        return None
