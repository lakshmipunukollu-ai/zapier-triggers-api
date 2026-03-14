"""Seed script — populate database with sample data for development."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.models.event import Event, DeliveryStatus
from app.models.subscription import Subscription
from app.services.event_service import compute_idempotency_key


def seed():
    """Create sample events and subscriptions."""
    init_db()
    db = SessionLocal()

    # Sample events
    sample_events = [
        {"source": "github.com", "event_type": "push", "payload": {"repo": "zapier/triggers", "branch": "main", "commits": 3}},
        {"source": "github.com", "event_type": "pull_request.opened", "payload": {"repo": "zapier/triggers", "pr_number": 42, "title": "Add retry logic"}},
        {"source": "stripe", "event_type": "payment.succeeded", "payload": {"amount": 9900, "currency": "usd", "customer_id": "cus_abc123"}},
        {"source": "stripe", "event_type": "invoice.created", "payload": {"invoice_id": "inv_xyz789", "amount_due": 4999}},
        {"source": "custom-app", "event_type": "order.created", "payload": {"order_id": "ord_001", "items": ["widget", "gadget"], "total": 59.99}},
        {"source": "custom-app", "event_type": "user.signup", "payload": {"user_id": "usr_new", "email": "user@example.com"}},
    ]

    for evt_data in sample_events:
        key = compute_idempotency_key(evt_data["source"], evt_data["event_type"], evt_data["payload"])
        existing = db.query(Event).filter(Event.idempotency_key == key).first()
        if not existing:
            event = Event(
                source=evt_data["source"],
                event_type=evt_data["event_type"],
                payload=evt_data["payload"],
                idempotency_key=key,
            )
            db.add(event)
            print(f"  Created event: {evt_data['source']}/{evt_data['event_type']}")

    # Sample subscriptions
    sample_subs = [
        {"consumer_id": "service-a", "event_type": "push", "source": "github.com", "webhook_url": "https://example.com/webhook/github"},
        {"consumer_id": "service-a", "event_type": "payment.succeeded", "source": "stripe", "webhook_url": "https://example.com/webhook/stripe"},
        {"consumer_id": "service-b", "source": "custom-app"},
    ]

    for sub_data in sample_subs:
        existing = db.query(Subscription).filter(
            Subscription.consumer_id == sub_data["consumer_id"],
            Subscription.event_type == sub_data.get("event_type"),
            Subscription.source == sub_data.get("source"),
        ).first()
        if not existing:
            sub = Subscription(**sub_data)
            db.add(sub)
            print(f"  Created subscription: {sub_data['consumer_id']} -> {sub_data.get('event_type', '*')}")

    db.commit()
    db.close()
    print("Seed complete!")


if __name__ == "__main__":
    seed()
