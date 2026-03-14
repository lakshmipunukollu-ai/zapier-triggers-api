"""Tests for event ingestion, inbox, ack, delete, and status endpoints."""
import time


def test_create_event(client):
    """POST /v1/events should create a new event."""
    response = client.post("/v1/events", json={
        "source": "github.com",
        "event_type": "push",
        "payload": {"repo": "test", "branch": "main"},
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("evt_")
    assert data["source"] == "github.com"
    assert data["event_type"] == "push"
    assert data["delivery_status"] == "pending"
    assert data["payload"]["repo"] == "test"


def test_create_event_validation_empty_source(client):
    """POST /v1/events with empty source should fail validation."""
    response = client.post("/v1/events", json={
        "source": "",
        "event_type": "push",
        "payload": {"key": "value"},
    })
    assert response.status_code == 422


def test_create_event_missing_fields(client):
    """POST /v1/events with missing required fields should fail."""
    response = client.post("/v1/events", json={
        "source": "test",
    })
    assert response.status_code == 422


def test_create_event_idempotency(client):
    """Duplicate events within idempotency window should return existing event."""
    payload = {
        "source": "stripe",
        "event_type": "payment.succeeded",
        "payload": {"amount": 100},
    }
    r1 = client.post("/v1/events", json=payload)
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    r2 = client.post("/v1/events", json=payload)
    # Duplicate returns 200 (via the router, which returns the existing event)
    assert r2.status_code in (200, 201)
    id2 = r2.json()["id"]

    assert id1 == id2


def test_create_different_events(client):
    """Different events should get different IDs."""
    r1 = client.post("/v1/events", json={
        "source": "github.com", "event_type": "push", "payload": {"a": 1},
    })
    r2 = client.post("/v1/events", json={
        "source": "github.com", "event_type": "push", "payload": {"a": 2},
    })
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


def test_inbox_returns_pending_events(client):
    """GET /v1/inbox should return pending events."""
    # Create some events
    client.post("/v1/events", json={
        "source": "src1", "event_type": "type1", "payload": {"n": 1},
    })
    client.post("/v1/events", json={
        "source": "src2", "event_type": "type2", "payload": {"n": 2},
    })

    response = client.get("/v1/inbox?consumer_id=test-consumer")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["events"]) == 2


def test_inbox_requires_consumer_id(client):
    """GET /v1/inbox without consumer_id should fail."""
    response = client.get("/v1/inbox")
    assert response.status_code == 422


def test_inbox_filter_by_source(client):
    """GET /v1/inbox with source filter should only return matching events."""
    client.post("/v1/events", json={
        "source": "github.com", "event_type": "push", "payload": {"n": 1},
    })
    client.post("/v1/events", json={
        "source": "stripe", "event_type": "charge", "payload": {"n": 2},
    })

    response = client.get("/v1/inbox?consumer_id=test&source=github.com")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["events"][0]["source"] == "github.com"


def test_inbox_filter_by_event_type(client):
    """GET /v1/inbox with event_type filter should only return matching events."""
    client.post("/v1/events", json={
        "source": "app", "event_type": "order.created", "payload": {"n": 1},
    })
    client.post("/v1/events", json={
        "source": "app", "event_type": "order.shipped", "payload": {"n": 2},
    })

    response = client.get("/v1/inbox?consumer_id=test&event_type=order.created")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["events"][0]["event_type"] == "order.created"


def test_inbox_limit(client):
    """GET /v1/inbox with limit should respect the limit."""
    for i in range(5):
        client.post("/v1/events", json={
            "source": "app", "event_type": "test", "payload": {"n": i},
        })

    response = client.get("/v1/inbox?consumer_id=test&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2


def test_ack_event(client):
    """POST /v1/events/:id/ack should acknowledge the event."""
    r = client.post("/v1/events", json={
        "source": "test", "event_type": "test", "payload": {"key": "val"},
    })
    event_id = r.json()["id"]

    ack_response = client.post(f"/v1/events/{event_id}/ack", json={
        "consumer_id": "my-consumer",
    })
    assert ack_response.status_code == 200
    data = ack_response.json()
    assert data["id"] == event_id
    assert data["delivery_status"] == "acked"
    assert data["acked_at"] is not None


def test_ack_nonexistent_event(client):
    """POST /v1/events/:id/ack for nonexistent event should return 404."""
    response = client.post("/v1/events/evt_doesnotexist0000/ack", json={
        "consumer_id": "test",
    })
    assert response.status_code == 404


def test_acked_events_not_in_inbox(client):
    """Acked events should not appear in the inbox."""
    r = client.post("/v1/events", json={
        "source": "test", "event_type": "test", "payload": {"key": "val"},
    })
    event_id = r.json()["id"]

    # Ack it
    client.post(f"/v1/events/{event_id}/ack", json={"consumer_id": "test"})

    # Check inbox
    inbox = client.get("/v1/inbox?consumer_id=test")
    assert inbox.json()["count"] == 0


def test_delete_event(client):
    """DELETE /v1/events/:id should remove the event."""
    r = client.post("/v1/events", json={
        "source": "test", "event_type": "test", "payload": {"key": "val"},
    })
    event_id = r.json()["id"]

    del_response = client.delete(f"/v1/events/{event_id}")
    assert del_response.status_code == 200
    data = del_response.json()
    assert data["deleted"] is True
    assert data["id"] == event_id


def test_delete_nonexistent_event(client):
    """DELETE /v1/events/:id for nonexistent event should return 404."""
    response = client.delete("/v1/events/evt_doesnotexist0000")
    assert response.status_code == 404


def test_deleted_event_not_in_inbox(client):
    """Deleted events should not appear in the inbox."""
    r = client.post("/v1/events", json={
        "source": "test", "event_type": "test", "payload": {"key": "val"},
    })
    event_id = r.json()["id"]
    client.delete(f"/v1/events/{event_id}")

    inbox = client.get("/v1/inbox?consumer_id=test")
    assert inbox.json()["count"] == 0


def test_event_status(client):
    """GET /v1/events/:id/status should return event details."""
    r = client.post("/v1/events", json={
        "source": "github.com", "event_type": "push", "payload": {"branch": "main"},
    })
    event_id = r.json()["id"]

    status_response = client.get(f"/v1/events/{event_id}/status")
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["id"] == event_id
    assert data["source"] == "github.com"
    assert data["event_type"] == "push"
    assert data["delivery_status"] == "pending"
    assert data["delivery_attempts"] == 0
    assert isinstance(data["delivery_log"], list)


def test_event_status_nonexistent(client):
    """GET /v1/events/:id/status for nonexistent event should return 404."""
    response = client.get("/v1/events/evt_doesnotexist0000/status")
    assert response.status_code == 404
