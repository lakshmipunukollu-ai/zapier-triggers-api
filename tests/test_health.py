"""Tests for health check endpoint."""


def test_health_endpoint(client):
    """Health endpoint should return status info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
