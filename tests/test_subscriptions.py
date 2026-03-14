"""Tests for subscription CRUD endpoints."""


def test_create_subscription(client):
    """POST /v1/subscriptions should create a new subscription."""
    response = client.post("/v1/subscriptions", json={
        "consumer_id": "service-a",
        "event_type": "push",
        "source": "github.com",
        "webhook_url": "https://example.com/webhook",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("sub_")
    assert data["consumer_id"] == "service-a"
    assert data["event_type"] == "push"
    assert data["source"] == "github.com"
    assert data["webhook_url"] == "https://example.com/webhook"
    assert data["is_active"] is True


def test_create_subscription_minimal(client):
    """POST /v1/subscriptions with only consumer_id should work."""
    response = client.post("/v1/subscriptions", json={
        "consumer_id": "service-b",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["consumer_id"] == "service-b"
    assert data["event_type"] is None
    assert data["source"] is None
    assert data["webhook_url"] is None


def test_create_subscription_missing_consumer_id(client):
    """POST /v1/subscriptions without consumer_id should fail."""
    response = client.post("/v1/subscriptions", json={
        "event_type": "push",
    })
    assert response.status_code == 422


def test_list_subscriptions(client):
    """GET /v1/subscriptions should return all subscriptions."""
    client.post("/v1/subscriptions", json={"consumer_id": "svc-a", "event_type": "push"})
    client.post("/v1/subscriptions", json={"consumer_id": "svc-b", "event_type": "pull"})

    response = client.get("/v1/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["subscriptions"]) == 2


def test_list_subscriptions_filter_consumer(client):
    """GET /v1/subscriptions with consumer_id filter should return only matching."""
    client.post("/v1/subscriptions", json={"consumer_id": "svc-a", "event_type": "push"})
    client.post("/v1/subscriptions", json={"consumer_id": "svc-b", "event_type": "pull"})

    response = client.get("/v1/subscriptions?consumer_id=svc-a")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["subscriptions"][0]["consumer_id"] == "svc-a"


def test_get_subscription_by_id(client):
    """GET /v1/subscriptions/:id should return the subscription."""
    r = client.post("/v1/subscriptions", json={
        "consumer_id": "svc-x", "event_type": "test",
    })
    sub_id = r.json()["id"]

    response = client.get(f"/v1/subscriptions/{sub_id}")
    assert response.status_code == 200
    assert response.json()["id"] == sub_id


def test_get_nonexistent_subscription(client):
    """GET /v1/subscriptions/:id for nonexistent should return 404."""
    response = client.get("/v1/subscriptions/sub_doesnotexist0000")
    assert response.status_code == 404


def test_delete_subscription(client):
    """DELETE /v1/subscriptions/:id should remove the subscription."""
    r = client.post("/v1/subscriptions", json={"consumer_id": "svc-del"})
    sub_id = r.json()["id"]

    del_response = client.delete(f"/v1/subscriptions/{sub_id}")
    assert del_response.status_code == 200
    assert del_response.json()["deleted"] is True

    # Verify it's gone
    get_response = client.get(f"/v1/subscriptions/{sub_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_subscription(client):
    """DELETE /v1/subscriptions/:id for nonexistent should return 404."""
    response = client.delete("/v1/subscriptions/sub_doesnotexist0000")
    assert response.status_code == 404
