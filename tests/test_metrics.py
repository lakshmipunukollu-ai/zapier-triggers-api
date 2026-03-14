"""Tests for metrics endpoint."""


def test_metrics_empty(client):
    """GET /v1/metrics should return zeroes when no events exist."""
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 0
    assert data["pending"] == 0
    assert data["delivered"] == 0
    assert data["acked"] == 0
    assert data["failed"] == 0
    assert data["dead"] == 0
    assert data["avg_delivery_time_ms"] == 0.0


def test_metrics_after_events(client):
    """GET /v1/metrics should reflect event counts."""
    # Create events
    client.post("/v1/events", json={
        "source": "test", "event_type": "a", "payload": {"n": 1},
    })
    client.post("/v1/events", json={
        "source": "test", "event_type": "b", "payload": {"n": 2},
    })

    response = client.get("/v1/metrics")
    data = response.json()
    assert data["total_events"] == 2
    assert data["pending"] == 2


def test_metrics_after_ack(client):
    """Metrics should update after acknowledging events."""
    r = client.post("/v1/events", json={
        "source": "test", "event_type": "a", "payload": {"n": 1},
    })
    event_id = r.json()["id"]
    client.post(f"/v1/events/{event_id}/ack", json={"consumer_id": "test"})

    response = client.get("/v1/metrics")
    data = response.json()
    assert data["total_events"] == 1
    assert data["acked"] == 1
    assert data["pending"] == 0
