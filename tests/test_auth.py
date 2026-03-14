"""Tests for authentication endpoints and middleware."""


def test_generate_token(client):
    """POST /auth/token should return a JWT token."""
    response = client.post("/auth/token", json={
        "user_id": "test-user",
        "role": "admin",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_authenticated_request(client):
    """Endpoints should work with a valid JWT token."""
    # Get token
    token_response = client.post("/auth/token", json={
        "user_id": "test-user",
    })
    token = token_response.json()["access_token"]

    # Use token to access endpoint
    response = client.get("/v1/metrics", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200


def test_unauthenticated_request_allowed_in_dev(client):
    """Endpoints should allow unauthenticated access in dev mode."""
    response = client.get("/v1/metrics")
    assert response.status_code == 200


def test_invalid_token(client):
    """Invalid tokens should return 401."""
    response = client.get("/v1/metrics", headers={
        "Authorization": "Bearer invalid-token-here",
    })
    assert response.status_code == 401
