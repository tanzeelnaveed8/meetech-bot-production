from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from src.db.connection import get_db_session
from src.db.redis_client import get_redis_client
from src.repositories.proof_asset_repository import ProofAssetRepository
from src.repositories.lead_repository import LeadRepository
from src.repositories.conversation_repository import ConversationRepository
from src.services.analytics_service import AnalyticsService
from src.models.enums import AssetType

router = APIRouter(prefix="/admin")


# Request/Response Models
class ProofAssetCreate(BaseModel):
    """Request model for creating a proof asset."""
    asset_type: AssetType
    project_type: str
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_text: Optional[str] = None


class ProofAssetUpdate(BaseModel):
    """Request model for updating a proof asset."""
    asset_type: Optional[AssetType] = None
    project_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_text: Optional[str] = None


class ProofAssetResponse(BaseModel):
    """Response model for proof asset."""
    id: UUID
    asset_type: AssetType
    project_type: str
    title: str
    description: Optional[str]
    content_url: Optional[str]
    content_text: Optional[str]
    usage_count: int
    last_used_at: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class BotStatusResponse(BaseModel):
    """Response model for bot status."""
    is_active: bool
    paused_at: Optional[str]
    paused_by: Optional[str]
    reason: Optional[str]


class BlacklistEntry(BaseModel):
    """Request/Response model for blacklist entry."""
    phone_number: str
    reason: Optional[str] = None
    added_at: Optional[str] = None


class ResponseTemplateUpdate(BaseModel):
    """Request model for updating response template."""
    template_key: str
    template_text: str


class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""
    total_leads: int
    total_conversations: int
    total_messages: int
    active_conversations: int
    avg_response_time_ms: float
    leads_by_score_category: Dict[str, int]
    leads_by_state: Dict[str, int]
    conversion_rate: float
    top_project_types: List[Dict[str, Any]]


# Endpoints
@router.get("/proof-assets", response_model=List[ProofAssetResponse])
async def list_proof_assets(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all proof assets.

    Args:
        active_only: If True, only return active assets
        db: Database session

    Returns:
        List of proof assets
    """
    repo = ProofAssetRepository(db)

    if active_only:
        assets = await repo.list_active()
    else:
        assets = await repo.list_active(limit=1000)  # Get all

    return [
        ProofAssetResponse(
            id=asset.id,
            asset_type=asset.asset_type,
            project_type=asset.project_type,
            title=asset.title,
            description=asset.description,
            content_url=asset.content_url,
            content_text=asset.content_text,
            usage_count=asset.usage_count,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            is_active=asset.is_active,
            created_at=asset.created_at.isoformat()
        )
        for asset in assets
    ]


@router.post("/proof-assets", response_model=ProofAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_proof_asset(
    asset_data: ProofAssetCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new proof asset.

    Args:
        asset_data: Proof asset data
        db: Database session

    Returns:
        Created proof asset
    """
    repo = ProofAssetRepository(db)

    asset = await repo.create(
        asset_type=asset_data.asset_type,
        project_type=asset_data.project_type,
        title=asset_data.title,
        description=asset_data.description,
        content_url=asset_data.content_url,
        content_text=asset_data.content_text
    )

    await db.commit()

    return ProofAssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        project_type=asset.project_type,
        title=asset.title,
        description=asset.description,
        content_url=asset.content_url,
        content_text=asset.content_text,
        usage_count=asset.usage_count,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        is_active=asset.is_active,
        created_at=asset.created_at.isoformat()
    )


@router.get("/proof-assets/{asset_id}", response_model=ProofAssetResponse)
async def get_proof_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific proof asset by ID.

    Args:
        asset_id: Proof asset ID
        db: Database session

    Returns:
        Proof asset details
    """
    repo = ProofAssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof asset {asset_id} not found"
        )

    return ProofAssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        project_type=asset.project_type,
        title=asset.title,
        description=asset.description,
        content_url=asset.content_url,
        content_text=asset.content_text,
        usage_count=asset.usage_count,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        is_active=asset.is_active,
        created_at=asset.created_at.isoformat()
    )


@router.put("/proof-assets/{asset_id}", response_model=ProofAssetResponse)
async def update_proof_asset(
    asset_id: UUID,
    asset_data: ProofAssetUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update a proof asset.

    Args:
        asset_id: Proof asset ID
        asset_data: Updated asset data
        db: Database session

    Returns:
        Updated proof asset
    """
    repo = ProofAssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof asset {asset_id} not found"
        )

    # Update fields if provided
    if asset_data.asset_type is not None:
        asset.asset_type = asset_data.asset_type
    if asset_data.project_type is not None:
        asset.project_type = asset_data.project_type
    if asset_data.title is not None:
        asset.title = asset_data.title
    if asset_data.description is not None:
        asset.description = asset_data.description
    if asset_data.content_url is not None:
        asset.content_url = asset_data.content_url
    if asset_data.content_text is not None:
        asset.content_text = asset_data.content_text

    await repo.update(asset)
    await db.commit()

    return ProofAssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        project_type=asset.project_type,
        title=asset.title,
        description=asset.description,
        content_url=asset.content_url,
        content_text=asset.content_text,
        usage_count=asset.usage_count,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        is_active=asset.is_active,
        created_at=asset.created_at.isoformat()
    )


@router.patch("/proof-assets/{asset_id}/activate", response_model=ProofAssetResponse)
async def activate_proof_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Activate a proof asset.

    Args:
        asset_id: Proof asset ID
        db: Database session

    Returns:
        Activated proof asset
    """
    repo = ProofAssetRepository(db)
    asset = await repo.activate(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof asset {asset_id} not found"
        )

    await db.commit()

    return ProofAssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        project_type=asset.project_type,
        title=asset.title,
        description=asset.description,
        content_url=asset.content_url,
        content_text=asset.content_text,
        usage_count=asset.usage_count,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        is_active=asset.is_active,
        created_at=asset.created_at.isoformat()
    )


@router.patch("/proof-assets/{asset_id}/deactivate", response_model=ProofAssetResponse)
async def deactivate_proof_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Deactivate a proof asset (soft delete).

    Args:
        asset_id: Proof asset ID
        db: Database session

    Returns:
        Deactivated proof asset
    """
    repo = ProofAssetRepository(db)
    asset = await repo.deactivate(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof asset {asset_id} not found"
        )

    await db.commit()

    return ProofAssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        project_type=asset.project_type,
        title=asset.title,
        description=asset.description,
        content_url=asset.content_url,
        content_text=asset.content_text,
        usage_count=asset.usage_count,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        is_active=asset.is_active,
        created_at=asset.created_at.isoformat()
    )


@router.delete("/proof-assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proof_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a proof asset (hard delete).

    Args:
        asset_id: Proof asset ID
        db: Database session

    Returns:
        No content
    """
    repo = ProofAssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proof asset {asset_id} not found"
        )

    await repo.delete(asset_id)
    await db.commit()

    return None


# ============================================================================
# Bot Control Endpoints (T105, T106, T107)
# ============================================================================

@router.post("/bot/pause", response_model=BotStatusResponse)
async def pause_bot(
    reason: Optional[str] = None,
    paused_by: Optional[str] = "admin"
):
    """
    Pause the bot globally. All incoming messages will be queued but not processed.

    Args:
        reason: Reason for pausing the bot
        paused_by: Admin user who paused the bot

    Returns:
        Bot status
    """
    redis = await get_redis_client()

    pause_data = {
        "is_active": False,
        "paused_at": datetime.utcnow().isoformat(),
        "paused_by": paused_by,
        "reason": reason or "Manual pause by admin"
    }

    await redis.set("bot:status", str(pause_data))

    return BotStatusResponse(**pause_data)


@router.post("/bot/resume", response_model=BotStatusResponse)
async def resume_bot():
    """
    Resume the bot globally. Bot will start processing messages again.

    Returns:
        Bot status
    """
    redis = await get_redis_client()

    resume_data = {
        "is_active": True,
        "paused_at": None,
        "paused_by": None,
        "reason": None
    }

    await redis.set("bot:status", str(resume_data))

    return BotStatusResponse(**resume_data)


@router.get("/bot/status", response_model=BotStatusResponse)
async def get_bot_status():
    """
    Get current bot status (active/paused).

    Returns:
        Bot status
    """
    redis = await get_redis_client()

    status_data = await redis.get("bot:status")

    if not status_data:
        # Default: bot is active
        return BotStatusResponse(
            is_active=True,
            paused_at=None,
            paused_by=None,
            reason=None
        )

    # Parse stored status
    import ast
    status_dict = ast.literal_eval(status_data)
    return BotStatusResponse(**status_dict)


# ============================================================================
# Blacklist Management Endpoints (T110)
# ============================================================================

@router.get("/blacklist", response_model=List[BlacklistEntry])
async def list_blacklist():
    """
    List all blacklisted phone numbers.

    Returns:
        List of blacklisted entries
    """
    redis = await get_redis_client()

    # Get all blacklist keys
    keys = await redis.keys("blacklist:*")

    blacklist = []
    for key in keys:
        phone_number = key.decode().replace("blacklist:", "")
        data = await redis.get(key)

        if data:
            import ast
            entry_data = ast.literal_eval(data.decode())
            blacklist.append(BlacklistEntry(
                phone_number=phone_number,
                reason=entry_data.get("reason"),
                added_at=entry_data.get("added_at")
            ))

    return blacklist


@router.post("/blacklist", response_model=BlacklistEntry, status_code=status.HTTP_201_CREATED)
async def add_to_blacklist(entry: BlacklistEntry):
    """
    Add a phone number to the blacklist.

    Args:
        entry: Blacklist entry with phone number and reason

    Returns:
        Created blacklist entry
    """
    redis = await get_redis_client()

    entry_data = {
        "phone_number": entry.phone_number,
        "reason": entry.reason or "Blacklisted by admin",
        "added_at": datetime.utcnow().isoformat()
    }

    await redis.set(f"blacklist:{entry.phone_number}", str(entry_data))

    return BlacklistEntry(**entry_data)


@router.delete("/blacklist/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_blacklist(phone_number: str):
    """
    Remove a phone number from the blacklist.

    Args:
        phone_number: Phone number to remove

    Returns:
        No content
    """
    redis = await get_redis_client()

    deleted = await redis.delete(f"blacklist:{phone_number}")

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number {phone_number} not found in blacklist"
        )

    return None


# ============================================================================
# Response Template Management Endpoints (T108, T109)
# ============================================================================

@router.get("/responses", response_model=Dict[str, str])
async def list_response_templates():
    """
    List all response templates.

    Returns:
        Dictionary of template keys and texts
    """
    redis = await get_redis_client()

    # Get all response template keys
    keys = await redis.keys("response_template:*")

    templates = {}
    for key in keys:
        template_key = key.decode().replace("response_template:", "")
        template_text = await redis.get(key)

        if template_text:
            templates[template_key] = template_text.decode()

    # If no templates in Redis, return defaults
    if not templates:
        templates = {
            "greeting": "Hi! Thanks for reaching out. How can I help you today?",
            "qualification_start": "Great! Let me ask you a few questions to better understand your needs.",
            "pricing_defer": "Pricing is customized based on your specific needs. Let me connect you with our team.",
            "follow_up_inactive": "Hi! Just following up on our previous conversation. Are you still interested?",
            "follow_up_call_not_booked": "Hi! Would you like to schedule a call to discuss your project?",
        }

    return templates


@router.put("/responses/{template_key}", response_model=Dict[str, str])
async def update_response_template(template_key: str, update: ResponseTemplateUpdate):
    """
    Update a response template.

    Args:
        template_key: Template key to update
        update: New template text

    Returns:
        Updated template
    """
    redis = await get_redis_client()

    await redis.set(f"response_template:{template_key}", update.template_text)

    return {template_key: update.template_text}


# ============================================================================
# Analytics Endpoint (T111)
# ============================================================================

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db_session)):
    """
    Get system analytics and metrics.

    Args:
        db: Database session

    Returns:
        Analytics data
    """
    analytics_service = AnalyticsService(db)

    analytics_data = await analytics_service.get_dashboard_metrics()

    return AnalyticsResponse(**analytics_data)
