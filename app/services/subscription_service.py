"""Subscription service — business logic for managing event subscriptions."""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.subscription import Subscription


def create_subscription(
    db: Session,
    consumer_id: str,
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    webhook_url: Optional[str] = None,
) -> Subscription:
    """Create a new subscription."""
    sub = Subscription(
        consumer_id=consumer_id,
        event_type=event_type,
        source=source,
        webhook_url=webhook_url,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def list_subscriptions(
    db: Session,
    consumer_id: Optional[str] = None,
) -> List[Subscription]:
    """List subscriptions, optionally filtered by consumer_id."""
    query = db.query(Subscription)
    if consumer_id:
        query = query.filter(Subscription.consumer_id == consumer_id)
    return query.order_by(Subscription.created_at.desc()).all()


def get_subscription(db: Session, subscription_id: str) -> Optional[Subscription]:
    """Get a subscription by ID."""
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()


def delete_subscription(db: Session, subscription_id: str) -> bool:
    """Delete a subscription."""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        return False
    db.delete(sub)
    db.commit()
    return True


def get_matching_subscriptions(
    db: Session,
    event_type: str,
    source: str,
) -> List[Subscription]:
    """Find active subscriptions matching an event's type and source."""
    return (
        db.query(Subscription)
        .filter(Subscription.is_active == True)
        .filter(
            (Subscription.event_type.is_(None)) | (Subscription.event_type == event_type)
        )
        .filter(
            (Subscription.source.is_(None)) | (Subscription.source == source)
        )
        .filter(Subscription.webhook_url.isnot(None))
        .all()
    )
