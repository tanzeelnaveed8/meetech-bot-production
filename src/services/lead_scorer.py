from typing import Dict, Any, Optional
from src.models.enums import ScoreCategory
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LeadScorer:
    """Lead scoring engine that calculates lead quality based on multiple factors."""

    def __init__(self):
        # Score ranges per constitution
        self.score_ranges = {
            ScoreCategory.LOW: (0, 39),
            ScoreCategory.MEDIUM: (40, 69),
            ScoreCategory.HIGH: (70, 100),
        }

    def calculate_total_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate total lead score based on all components.

        Args:
            lead_data: Dict with lead information

        Returns:
            Dict with total_score, component scores, category, and reasoning
        """
        # Calculate component scores (FR-007)
        budget_score = self.calculate_budget_score(
            lead_data.get("budget_numeric"),
            lead_data.get("budget_avoidance_count", 0)
        )

        timeline_score = self.calculate_timeline_score(
            lead_data.get("timeline")
        )

        clarity_score = self.calculate_clarity_score(
            lead_data.get("project_type"),
            lead_data.get("timeline") is not None,
            lead_data.get("budget_numeric") is not None,
            lead_data.get("message_count", 0)
        )

        country_score = self.calculate_country_score(
            lead_data.get("country")
        )

        behavior_score = self.calculate_behavior_score(
            lead_data.get("budget_avoidance_count", 0),
            lead_data.get("message_count", 0),
            lead_data.get("response_pattern", "normal")
        )

        # Calculate total (FR-008: 0-100 scale)
        total_score = (
            budget_score +
            timeline_score +
            clarity_score +
            country_score +
            behavior_score
        )

        # Determine category
        score_category = self._categorize_score(total_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            budget_score, timeline_score, clarity_score,
            country_score, behavior_score, lead_data
        )

        logger.info(
            "Lead scored",
            total_score=total_score,
            category=score_category.value,
            budget=budget_score,
            timeline=timeline_score,
            clarity=clarity_score,
            country=country_score,
            behavior=behavior_score
        )

        return {
            "total_score": total_score,
            "budget_score": budget_score,
            "timeline_score": timeline_score,
            "clarity_score": clarity_score,
            "country_score": country_score,
            "behavior_score": behavior_score,
            "score_category": score_category,
            "reasoning": reasoning,
        }

    def calculate_budget_score(
        self,
        budget_numeric: Optional[int],
        budget_avoidance_count: int = 0
    ) -> int:
        """
        Calculate budget component score (0-30 points).

        Args:
            budget_numeric: Numeric budget value
            budget_avoidance_count: Number of times budget was avoided

        Returns:
            Budget score (0-30)
        """
        if budget_avoidance_count >= 2:
            # Budget avoidance flagged (FR-006)
            return 5  # Low score for avoidance

        if budget_numeric is None:
            return 0

        # Score based on budget ranges
        if budget_numeric >= 20000:
            return 30  # High budget
        elif budget_numeric >= 10000:
            return 25
        elif budget_numeric >= 7000:
            return 20
        elif budget_numeric >= 5000:
            return 15
        elif budget_numeric >= 3000:
            return 10
        else:
            return 5  # Low budget

    def calculate_timeline_score(self, timeline: Optional[str]) -> int:
        """
        Calculate timeline urgency score (0-25 points).

        Args:
            timeline: Timeline string

        Returns:
            Timeline score (0-25)
        """
        if not timeline:
            return 0

        timeline_lower = timeline.lower()

        # Urgent timelines get high scores
        if any(word in timeline_lower for word in ["urgent", "asap", "immediately", "1 week", "2 weeks"]):
            return 25

        # Short timelines (1-2 months)
        if any(word in timeline_lower for word in ["1 month", "2 months", "1-2 months"]):
            return 18

        # Medium timelines (2-3 months)
        if any(word in timeline_lower for word in ["2-3 months", "3 months"]):
            return 12

        # Flexible/long timelines
        if any(word in timeline_lower for word in ["flexible", "no rush", "6 months", "later"]):
            return 5

        # Default for specified timeline
        return 10

    def calculate_clarity_score(
        self,
        project_type: Optional[str],
        has_timeline: bool,
        has_budget: bool,
        message_count: int
    ) -> int:
        """
        Calculate requirement clarity score (0-20 points).

        Args:
            project_type: Type of project
            has_timeline: Whether timeline is specified
            has_budget: Whether budget is specified
            message_count: Number of messages exchanged

        Returns:
            Clarity score (0-20)
        """
        score = 0

        # Project type clarity
        if project_type:
            if project_type in ["e-commerce", "mobile-app", "custom-software"]:
                score += 8  # Specific project type
            else:
                score += 5  # General project type

        # Completeness of information
        if has_timeline:
            score += 4
        if has_budget:
            score += 4

        # Engagement level (more messages = more clarity)
        if message_count >= 6:
            score += 4
        elif message_count >= 4:
            score += 2

        return min(score, 20)  # Cap at 20

    def calculate_country_score(self, country: Optional[str]) -> int:
        """
        Calculate country/geography score (0-15 points).

        Args:
            country: Country code (ISO 3166-1 alpha-2)

        Returns:
            Country score (0-15)
        """
        if not country:
            return 7  # Neutral score if unknown

        # High-value markets
        high_value = ["US", "GB", "CA", "AU", "DE", "FR", "NL", "SE", "NO", "DK"]
        if country in high_value:
            return 15

        # Medium-value markets
        medium_value = ["IN", "BR", "MX", "ES", "IT", "PL", "SG", "AE"]
        if country in medium_value:
            return 10

        # Other markets
        return 7

    def calculate_behavior_score(
        self,
        budget_avoidance_count: int,
        message_count: int,
        response_pattern: str
    ) -> int:
        """
        Calculate message behavior score (0-10 points).

        Args:
            budget_avoidance_count: Number of budget avoidances
            message_count: Total messages
            response_pattern: Pattern of responses (engaged, evasive, normal)

        Returns:
            Behavior score (0-10)
        """
        score = 10  # Start with full points

        # Penalize budget avoidance
        score -= budget_avoidance_count * 2

        # Penalize very few messages (lack of engagement)
        if message_count < 3:
            score -= 3
        elif message_count < 5:
            score -= 1

        # Adjust for response pattern
        if response_pattern == "evasive":
            score -= 2
        elif response_pattern == "engaged":
            score += 0  # Already at max

        return max(0, min(score, 10))  # Clamp to 0-10

    def _categorize_score(self, total_score: int) -> ScoreCategory:
        """
        Categorize total score into LOW/MEDIUM/HIGH (FR-008).

        Args:
            total_score: Total score (0-100)

        Returns:
            Score category
        """
        if total_score >= 70:
            return ScoreCategory.HIGH
        elif total_score >= 40:
            return ScoreCategory.MEDIUM
        else:
            return ScoreCategory.LOW

    def _generate_reasoning(
        self,
        budget_score: int,
        timeline_score: int,
        clarity_score: int,
        country_score: int,
        behavior_score: int,
        lead_data: Dict[str, Any]
    ) -> str:
        """Generate human-readable score reasoning."""
        reasons = []

        # Budget reasoning
        if budget_score >= 25:
            reasons.append("High budget ($10k+)")
        elif budget_score >= 15:
            reasons.append("Medium budget ($5k-$10k)")
        elif lead_data.get("budget_avoidance_count", 0) >= 2:
            reasons.append("Budget information avoided")
        else:
            reasons.append("Low budget")

        # Timeline reasoning
        if timeline_score >= 20:
            reasons.append("Urgent timeline")
        elif timeline_score >= 10:
            reasons.append("Normal timeline")
        else:
            reasons.append("Flexible timeline")

        # Clarity reasoning
        if clarity_score >= 15:
            reasons.append("Clear requirements")
        elif clarity_score >= 10:
            reasons.append("Moderate clarity")
        else:
            reasons.append("Vague requirements")

        # Behavior reasoning
        if behavior_score >= 8:
            reasons.append("Engaged communication")
        elif behavior_score <= 5:
            reasons.append("Limited engagement")

        return "; ".join(reasons)
