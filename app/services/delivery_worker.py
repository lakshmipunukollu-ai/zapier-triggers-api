"""Background delivery worker — processes pending events and delivers to webhook URLs.

Implements exponential backoff retry with dead-letter handling.
"""
import asyncio
import logging
import time
from datetime import datetime

import httpx

from app.database import SessionLocal
from app.models.event import Event, DeliveryStatus
from app.models.delivery_log import DeliveryLog
from app.services.subscription_service import get_matching_subscriptions
from app.config import MAX_DELIVERY_ATTEMPTS, RETRY_DELAYS

logger = logging.getLogger(__name__)


async def deliver_event(event_id: str):
    """Attempt to deliver a single event to all matching webhook subscriptions."""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return

        if event.delivery_status in (DeliveryStatus.ACKED, DeliveryStatus.DEAD):
            return

        subscriptions = get_matching_subscriptions(db, event.event_type, event.source)
        if not subscriptions:
            # No webhooks to deliver to — mark as delivered (available for pull)
            event.delivery_status = DeliveryStatus.DELIVERED
            db.commit()
            return

        all_succeeded = True
        for sub in subscriptions:
            success = await _deliver_to_webhook(db, event, sub.webhook_url)
            if not success:
                all_succeeded = False

        if all_succeeded:
            event.delivery_status = DeliveryStatus.DELIVERED
        elif event.delivery_attempts >= MAX_DELIVERY_ATTEMPTS:
            event.delivery_status = DeliveryStatus.DEAD
            logger.warning(f"Event {event.id} moved to dead letter after {MAX_DELIVERY_ATTEMPTS} attempts")
        else:
            event.delivery_status = DeliveryStatus.FAILED

        event.last_attempt_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Error delivering event {event_id}: {e}")
        db.rollback()
    finally:
        db.close()


async def _deliver_to_webhook(db, event: Event, webhook_url: str) -> bool:
    """POST event payload to a webhook URL. Returns True on success."""
    event.delivery_attempts += 1
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "event_id": event.id,
                    "source": event.source,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "attempt": event.delivery_attempts,
                },
            )
        duration_ms = int((time.time() - start_time) * 1000)

        log = DeliveryLog(
            event_id=event.id,
            attempt_number=event.delivery_attempts,
            status_code=response.status_code,
            response_body=response.text[:1000] if response.text else None,
            duration_ms=duration_ms,
        )
        db.add(log)

        return 200 <= response.status_code < 300

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log = DeliveryLog(
            event_id=event.id,
            attempt_number=event.delivery_attempts,
            error_message=str(e)[:1000],
            duration_ms=duration_ms,
        )
        db.add(log)
        return False


async def process_pending_events(redis_client):
    """Background loop that processes events from the Redis pending queue."""
    logger.info("Delivery worker started")
    while True:
        try:
            event_id = redis_client.rpop("events:pending")
            if event_id:
                await deliver_event(event_id)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Delivery worker error: {e}")
            await asyncio.sleep(5)


async def retry_failed_events():
    """Background loop that retries failed events based on retry schedule."""
    logger.info("Retry scheduler started")
    while True:
        try:
            db = SessionLocal()
            failed_events = (
                db.query(Event)
                .filter(Event.delivery_status == DeliveryStatus.FAILED)
                .filter(Event.delivery_attempts < MAX_DELIVERY_ATTEMPTS)
                .all()
            )
            for event in failed_events:
                attempt_idx = min(event.delivery_attempts, len(RETRY_DELAYS) - 1)
                delay = RETRY_DELAYS[attempt_idx]
                if event.last_attempt_at:
                    elapsed = (datetime.utcnow() - event.last_attempt_at).total_seconds()
                    if elapsed >= delay:
                        event.delivery_status = DeliveryStatus.PENDING
                        from app.redis_client import redis_client
                        redis_client.lpush("events:pending", event.id)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Retry scheduler error: {e}")
        await asyncio.sleep(10)
