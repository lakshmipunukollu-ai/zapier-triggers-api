"""Subscription API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionListResponse,
)
from app.services.subscription_service import (
    create_subscription,
    list_subscriptions,
    get_subscription,
    delete_subscription,
)

router = APIRouter(prefix="/v1", tags=["subscriptions"])


@router.post(
    "/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subscription",
    description="Subscribe to events by type and/or source. Optionally provide a webhook URL for push delivery.",
)
def create_sub(
    body: SubscriptionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sub = create_subscription(
        db=db,
        consumer_id=body.consumer_id,
        event_type=body.event_type,
        source=body.source,
        webhook_url=body.webhook_url,
    )
    return sub


@router.get(
    "/subscriptions",
    response_model=SubscriptionListResponse,
    summary="List subscriptions",
    description="List all subscriptions, optionally filtered by consumer_id.",
)
def list_subs(
    consumer_id: str = Query(None, description="Filter by consumer ID"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    subs = list_subscriptions(db, consumer_id)
    return SubscriptionListResponse(
        subscriptions=[SubscriptionResponse.model_validate(s, from_attributes=True) for s in subs],
        count=len(subs),
    )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription details",
)
def get_sub(
    subscription_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sub = get_subscription(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} not found")
    return sub


@router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a subscription",
)
def delete_sub(
    subscription_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deleted = delete_subscription(db, subscription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} not found")
    return {"deleted": True, "id": subscription_id}
