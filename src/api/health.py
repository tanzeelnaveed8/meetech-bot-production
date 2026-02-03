from fastapi import APIRouter, Response
from pydantic import BaseModel
from datetime import datetime

from src.utils.metrics import get_metrics, get_metrics_content_type

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    Constitution requirement: Track < 1 second p95 response time.
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )
