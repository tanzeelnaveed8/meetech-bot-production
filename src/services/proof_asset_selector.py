from typing import Optional, List
from datetime import datetime, timedelta

from src.models.proof_asset import ProofAsset
from src.models.enums import State


class ProofAssetSelector:
    """Service for selecting and injecting relevant proof assets during conversations."""

    # States where asset injection is appropriate
    INJECTION_STATES = [State.QUALIFICATION, State.PROOF_DELIVERY]

    # Max assets per conversation (constitution requirement)
    MAX_ASSETS_PER_CONVERSATION = 1

    def should_inject_asset(
        self,
        conversation_proof_asset_count: int,
        project_type: Optional[str],
        current_state: str
    ) -> bool:
        """
        Determine if an asset should be injected in the current conversation context.

        Args:
            conversation_proof_asset_count: Number of assets already shared in this conversation
            project_type: The lead's project type (e.g., "e-commerce", "mobile-app")
            current_state: Current conversation state

        Returns:
            True if asset should be injected, False otherwise
        """
        # Enforce max 1 asset per conversation
        if conversation_proof_asset_count >= self.MAX_ASSETS_PER_CONVERSATION:
            return False

        # Must have a project type to match against
        if not project_type:
            return False

        # Only inject in appropriate states
        if current_state not in [s.value for s in self.INJECTION_STATES]:
            return False

        return True

    def select_asset(
        self,
        project_type: str,
        available_assets: List[ProofAsset]
    ) -> Optional[ProofAsset]:
        """
        Select the most relevant proof asset for the given project type.

        Selection algorithm:
        1. Filter to active assets only
        2. Calculate relevance score for each asset
        3. Return asset with highest score
        4. Return None if no relevant assets found

        Args:
            project_type: The lead's project type
            available_assets: List of available proof assets

        Returns:
            Selected ProofAsset or None if no relevant match
        """
        if not available_assets:
            return None

        # Filter to active assets only
        active_assets = [a for a in available_assets if a.is_active]

        if not active_assets:
            return None

        # Calculate relevance score for each asset
        scored_assets = [
            (asset, self.calculate_relevance_score(asset, project_type))
            for asset in active_assets
        ]

        # Filter out assets with very low relevance (< 0.5)
        # Higher threshold ensures only truly relevant assets are selected
        relevant_assets = [(a, s) for a, s in scored_assets if s >= 0.5]

        if not relevant_assets:
            return None

        # Sort by score (descending) and return highest
        relevant_assets.sort(key=lambda x: x[1], reverse=True)

        return relevant_assets[0][0]

    def calculate_relevance_score(
        self,
        asset: ProofAsset,
        project_type: str
    ) -> float:
        """
        Calculate relevance score for an asset based on multiple factors.

        Scoring components:
        - Project type match: 0.0 to 0.6 (exact match = 0.6)
        - Usage count: 0.0 to 0.25 (lower count = higher)
        - Usage recency: 0.0 to 0.15 (less recent = higher)

        Args:
            asset: The proof asset to score
            project_type: The lead's project type

        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0

        # Component 1: Project type match (weight: 0.6)
        # Primary factor for relevance
        project_type_score = self._calculate_project_type_score(
            asset.project_type,
            project_type
        )
        score += project_type_score * 0.6

        # Component 2: Usage count (weight: 0.25)
        # Higher weight to prefer less-used assets
        usage_score = self._calculate_usage_score(asset.usage_count)
        score += usage_score * 0.25

        # Component 3: Usage recency (weight: 0.15)
        # Secondary factor to distribute usage over time
        recency_score = self._calculate_recency_score(asset.last_used_at)
        score += recency_score * 0.15

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_project_type_score(
        self,
        asset_project_type: str,
        lead_project_type: str
    ) -> float:
        """
        Calculate project type match score.

        Returns:
            1.0 for exact match, 0.0 for no match
        """
        if not asset_project_type or not lead_project_type:
            return 0.0

        # Normalize to lowercase for comparison
        asset_type = asset_project_type.lower().strip()
        lead_type = lead_project_type.lower().strip()

        # Exact match
        if asset_type == lead_type:
            return 1.0

        # Partial match (e.g., "e-commerce" in "e-commerce-website")
        if asset_type in lead_type or lead_type in asset_type:
            return 0.7

        # No match
        return 0.0

    def _calculate_recency_score(
        self,
        last_used_at: Optional[datetime]
    ) -> float:
        """
        Calculate recency score based on when asset was last used.

        Returns:
            1.0 for never used or used long ago, lower for recently used
        """
        if last_used_at is None:
            # Never used - highest score
            return 1.0

        days_since_use = (datetime.utcnow() - last_used_at).days

        # Score decreases as recency increases
        if days_since_use >= 30:
            return 1.0  # Used 30+ days ago
        elif days_since_use >= 14:
            return 0.8  # Used 14-29 days ago
        elif days_since_use >= 7:
            return 0.6  # Used 7-13 days ago
        elif days_since_use >= 3:
            return 0.4  # Used 3-6 days ago
        else:
            return 0.2  # Used in last 3 days

    def _calculate_usage_score(self, usage_count: int) -> float:
        """
        Calculate usage score based on how many times asset has been used.

        Returns:
            1.0 for never used, decreasing as usage increases
        """
        if usage_count == 0:
            return 1.0  # Never used - highest score
        elif usage_count == 1:
            return 0.95
        elif usage_count == 2:
            return 0.9
        elif usage_count == 3:
            return 0.85
        elif usage_count == 4:
            return 0.8
        elif usage_count == 5:
            return 0.75
        elif usage_count <= 10:
            return 0.6
        elif usage_count <= 20:
            return 0.4
        elif usage_count <= 50:
            return 0.2
        else:
            return 0.1  # Heavily used

    def format_asset_message(self, asset: ProofAsset) -> str:
        """
        Format proof asset into a WhatsApp message.

        Args:
            asset: The proof asset to format

        Returns:
            Formatted message string
        """
        message_parts = []

        # Add title
        if asset.title:
            message_parts.append(f"📁 {asset.title}")

        # Add description
        if asset.description:
            message_parts.append(asset.description)

        # Add content text (for testimonials and case studies)
        if asset.content_text:
            message_parts.append(f"\n{asset.content_text}")

        # Add content URL (for portfolio images)
        if asset.content_url:
            message_parts.append(f"\n🔗 {asset.content_url}")

        return "\n".join(message_parts)
