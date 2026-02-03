from typing import List, Set
import re


class ContentFilter:
    """Content filter for brand-safe language validation."""

    def __init__(self):
        # Default blacklisted words/phrases (can be extended via admin API)
        self.blacklist: Set[str] = {
            # Profanity examples (add more as needed)
            "profanity1",
            "profanity2",
            # Add actual blacklisted terms
        }

        # Patterns to detect
        self.patterns = [
            r'\b(payment|pay|credit card|bank account)\b',  # Payment-related
            r'\b(price|cost|how much)\b',  # Pricing (should defer to human)
        ]

    def add_to_blacklist(self, phrase: str) -> None:
        """Add phrase to blacklist."""
        self.blacklist.add(phrase.lower())

    def remove_from_blacklist(self, phrase: str) -> None:
        """Remove phrase from blacklist."""
        self.blacklist.discard(phrase.lower())

    def contains_blacklisted_content(self, text: str) -> bool:
        """Check if text contains blacklisted content."""
        text_lower = text.lower()

        # Check blacklist
        for phrase in self.blacklist:
            if phrase in text_lower:
                return True

        return False

    def contains_pricing_intent(self, text: str) -> bool:
        """Check if text contains pricing-related intent."""
        text_lower = text.lower()
        pricing_keywords = [
            "price", "cost", "how much", "pricing", "quote",
            "estimate", "budget", "payment", "pay"
        ]

        return any(keyword in text_lower for keyword in pricing_keywords)

    def is_brand_safe(self, text: str) -> bool:
        """
        Check if text is brand-safe (no profanity, inappropriate content).

        Returns:
            True if brand-safe, False otherwise
        """
        return not self.contains_blacklisted_content(text)

    def sanitize_response(self, text: str) -> str:
        """
        Sanitize bot response to ensure brand safety.

        Args:
            text: Response text to sanitize

        Returns:
            Sanitized text
        """
        # Remove any blacklisted content
        sanitized = text

        for phrase in self.blacklist:
            # Replace with asterisks
            sanitized = re.sub(
                re.escape(phrase),
                "*" * len(phrase),
                sanitized,
                flags=re.IGNORECASE
            )

        return sanitized

    def validate_message_length(self, text: str, max_length: int = 300) -> bool:
        """
        Validate message length (constitution: 1-3 sentences, max 300 chars).

        Returns:
            True if valid length, False otherwise
        """
        return len(text) <= max_length

    def enforce_brevity(self, text: str, max_length: int = 300) -> str:
        """
        Enforce brevity constraint by truncating if needed.

        Args:
            text: Text to enforce brevity on
            max_length: Maximum character length

        Returns:
            Truncated text if needed
        """
        if len(text) <= max_length:
            return text

        # Truncate at sentence boundary if possible
        truncated = text[:max_length]
        last_period = truncated.rfind('.')

        if last_period > max_length * 0.7:  # If we can keep 70%+ of content
            return truncated[:last_period + 1]

        return truncated + "..."


# Global content filter instance
_content_filter = ContentFilter()


def get_content_filter() -> ContentFilter:
    """Get global content filter instance."""
    return _content_filter
