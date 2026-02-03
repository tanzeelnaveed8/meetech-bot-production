from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from src.models.proof_asset import ProofAsset
from src.models.enums import AssetType


class ProofAssetRepository:
    """Repository for ProofAsset CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        asset_type: AssetType,
        project_type: str,
        title: str,
        description: Optional[str] = None,
        content_url: Optional[str] = None,
        content_text: Optional[str] = None
    ) -> ProofAsset:
        """Create a new proof asset."""
        asset = ProofAsset(
            asset_type=asset_type,
            project_type=project_type,
            title=title,
            description=description,
            content_url=content_url,
            content_text=content_text
        )
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def get_by_id(self, asset_id: UUID) -> Optional[ProofAsset]:
        """Get proof asset by ID."""
        result = await self.session.execute(
            select(ProofAsset).where(ProofAsset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self, limit: int = 100) -> List[ProofAsset]:
        """List all active proof assets."""
        result = await self.session.execute(
            select(ProofAsset)
            .where(ProofAsset.is_active == True)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_project_type(
        self,
        project_type: str,
        active_only: bool = True
    ) -> List[ProofAsset]:
        """List proof assets by project type."""
        query = select(ProofAsset).where(ProofAsset.project_type == project_type)

        if active_only:
            query = query.where(ProofAsset.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_asset_type(
        self,
        asset_type: AssetType,
        active_only: bool = True
    ) -> List[ProofAsset]:
        """List proof assets by asset type."""
        query = select(ProofAsset).where(ProofAsset.asset_type == asset_type)

        if active_only:
            query = query.where(ProofAsset.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, asset: ProofAsset) -> ProofAsset:
        """Update proof asset."""
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def increment_usage(self, asset_id: UUID) -> ProofAsset:
        """Increment usage count and update last_used_at."""
        asset = await self.get_by_id(asset_id)
        if asset:
            asset.usage_count += 1
            asset.last_used_at = datetime.utcnow()
            await self.session.flush()
        return asset

    async def deactivate(self, asset_id: UUID) -> Optional[ProofAsset]:
        """Deactivate a proof asset (soft delete)."""
        asset = await self.get_by_id(asset_id)
        if asset:
            asset.is_active = False
            await self.session.flush()
        return asset

    async def activate(self, asset_id: UUID) -> Optional[ProofAsset]:
        """Activate a proof asset."""
        asset = await self.get_by_id(asset_id)
        if asset:
            asset.is_active = True
            await self.session.flush()
        return asset

    async def delete(self, asset_id: UUID) -> None:
        """Delete proof asset (hard delete for admin cleanup)."""
        asset = await self.get_by_id(asset_id)
        if asset:
            await self.session.delete(asset)
            await self.session.flush()
