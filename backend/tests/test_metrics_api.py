from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_metrics_endpoint_returns_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200

    data = response.json()

    assert "requests" in data
    assert "latency" in data
    assert "requests_by_path" in data
    assert "requests_by_status" in data


def test_health_request_is_recorded_in_metrics():
    health_response = client.get("/health")

    assert health_response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200

    data = metrics_response.json()

    assert data["requests"]["total"] >= 1
    assert data["requests"]["successful"] >= 1
    assert data["requests_by_path"]["/health"] >= 1
    assert data["requests_by_status"]["200"] >= 1


def test_metrics_track_request_latency():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200

    data = response.json()

    assert data["latency"]["total_duration_ms"] >= 0
    assert data["latency"]["average_duration_ms"] >= 0
