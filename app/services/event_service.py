"""Event service — core business logic for event ingestion, retrieval, and lifecycle."""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.event import Event, DeliveryStatus
from app.models.delivery_log import DeliveryLog
from app.config import VISIBILITY_TIMEOUT_SECONDS, IDEMPOTENCY_WINDOW_SECONDS


def compute_idempotency_key(source: str, event_type: str, payload: dict) -> str:
    """Generate SHA256 hash for idempotency check."""
    raw = f"{source}:{event_type}:{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_event(
    db: Session,
    redis_client,
    source: str,
    event_type: str,
    payload: dict,
) -> tuple:
    """Create a new event. Returns (event, is_new) tuple.

    If an identical event exists within the idempotency window, returns the existing one.
    """
    idempotency_key = compute_idempotency_key(source, event_type, payload)

    # Check for duplicate within idempotency window
    cutoff = datetime.utcnow() - timedelta(seconds=IDEMPOTENCY_WINDOW_SECONDS)
    existing = (
        db.query(Event)
        .filter(Event.idempotency_key == idempotency_key)
        .filter(Event.created_at >= cutoff)
        .first()
    )
    if existing:
        return existing, False

    event = Event(
        source=source,
        event_type=event_type,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Push to Redis pending queue
    try:
        redis_client.lpush("events:pending", event.id)
    except Exception:
        pass  # Redis failure shouldn't block event creation

    return event, True


def get_inbox_events(
    db: Session,
    redis_client,
    consumer_id: str,
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 10,
) -> List[Event]:
    """Get pending events for a consumer with visibility timeout locking."""
    now = datetime.utcnow()
    query = db.query(Event).filter(
        Event.delivery_status == DeliveryStatus.PENDING,
    ).filter(
        (Event.locked_until.is_(None)) | (Event.locked_until < now)
    )

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if source:
        query = query.filter(Event.source == source)

    events = query.order_by(Event.created_at.asc()).limit(limit).all()

    # Lock events with visibility timeout
    lock_until = now + timedelta(seconds=VISIBILITY_TIMEOUT_SECONDS)
    for event in events:
        event.locked_until = lock_until
        event.consumer_id = consumer_id
        # Also set Redis lock for faster checking
        try:
            redis_client.setex(
                f"lock:{event.id}",
                VISIBILITY_TIMEOUT_SECONDS,
                consumer_id,
            )
        except Exception:
            pass

    db.commit()
    return events


def ack_event(db: Session, redis_client, event_id: str, consumer_id: str) -> Optional[Event]:
    """Acknowledge an event as consumed."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None

    event.delivery_status = DeliveryStatus.ACKED
    event.acked_at = datetime.utcnow()
    event.consumer_id = consumer_id
    event.locked_until = None
    db.commit()
    db.refresh(event)

    # Remove Redis lock
    try:
        redis_client.delete(f"lock:{event.id}")
    except Exception:
        pass

    return event


def delete_event(db: Session, redis_client, event_id: str) -> bool:
    """Delete an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return False

    # Delete delivery logs first
    db.query(DeliveryLog).filter(DeliveryLog.event_id == event_id).delete()
    db.delete(event)
    db.commit()

    # Clean up Redis
    try:
        redis_client.delete(f"lock:{event.id}")
    except Exception:
        pass

    return True


def get_event_status(db: Session, event_id: str) -> Optional[dict]:
    """Get event with delivery log."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None

    logs = (
        db.query(DeliveryLog)
        .filter(DeliveryLog.event_id == event_id)
        .order_by(DeliveryLog.attempt_number.asc())
        .all()
    )

    return {
        "event": event,
        "logs": logs,
    }


def get_metrics(db: Session) -> dict:
    """Calculate aggregate event metrics."""
    total = db.query(Event).count()
    pending = db.query(Event).filter(Event.delivery_status == DeliveryStatus.PENDING).count()
    delivered = db.query(Event).filter(Event.delivery_status == DeliveryStatus.DELIVERED).count()
    acked = db.query(Event).filter(Event.delivery_status == DeliveryStatus.ACKED).count()
    failed = db.query(Event).filter(Event.delivery_status == DeliveryStatus.FAILED).count()
    dead = db.query(Event).filter(Event.delivery_status == DeliveryStatus.DEAD).count()

    # Calculate average delivery time from delivery logs
    from sqlalchemy import func
    avg_result = (
        db.query(func.avg(DeliveryLog.duration_ms))
        .filter(DeliveryLog.status_code.isnot(None))
        .scalar()
    )
    avg_delivery_time_ms = float(avg_result) if avg_result else 0.0

    return {
        "total_events": total,
        "pending": pending,
        "delivered": delivered,
        "acked": acked,
        "failed": failed,
        "dead": dead,
        "avg_delivery_time_ms": round(avg_delivery_time_ms, 2),
    }
