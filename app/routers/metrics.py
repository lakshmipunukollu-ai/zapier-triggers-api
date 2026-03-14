"""Metrics API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.schemas.metrics import MetricsResponse
from app.services.event_service import get_metrics

router = APIRouter(prefix="/v1", tags=["metrics"])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="System metrics",
    description="Returns aggregate event statistics: counts by status and average delivery time.",
)
def metrics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_metrics(db)
