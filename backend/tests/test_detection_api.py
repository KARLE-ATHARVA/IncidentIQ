from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_user_project_and_service():
    email = f"detection-api-{uuid4()}@example.com"
    password = "testpassword123"

    # Register
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    # Login
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create project
    response = client.post(
        "/api/projects",
        json={
            "name": "Detection API Test Project",
        },
        headers=headers,
    )

    assert response.status_code == 201

    project_id = response.json()["id"]

    # Create service
    response = client.post(
        f"/api/projects/{project_id}/services",
        json={
            "name": "Checkout Detection Service",
        },
        headers=headers,
    )

    assert response.status_code == 201

    service_id = response.json()["id"]

    return headers, project_id, service_id


def test_detect_metric_event():
    headers, project_id, service_id = (
        create_user_project_and_service()
    )

    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # Create 20 historical normal observations
    # ---------------------------------------------------------

    historical_values = [
        100,
        101,
        99,
        100,
        102,
        98,
        101,
        100,
        99,
        102,
        100,
        101,
        98,
        100,
        102,
        99,
        101,
        100,
        99,
        101,
    ]

    for index, value in enumerate(historical_values):
        timestamp = now - timedelta(
            minutes=30 + (20 - index)
        )

        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/metrics",
            json={
                "timestamp": timestamp.isoformat(),
                "name": "checkout_latency",
                "value": value,
            },
            headers=headers,
        )

        assert response.status_code == 201

    # ---------------------------------------------------------
    # Create 5 recent anomalous observations
    # ---------------------------------------------------------

    for index in range(5):
        timestamp = now - timedelta(
            minutes=5 - index
        )

        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/metrics",
            json={
                "timestamp": timestamp.isoformat(),
                "name": "checkout_latency",
                "value": 165,
            },
            headers=headers,
        )

        assert response.status_code == 201

    # ---------------------------------------------------------
    # Create current metric event
    # ---------------------------------------------------------

    response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        json={
            "timestamp": now.isoformat(),
            "name": "checkout_latency",
            "value": 165,
        },
        headers=headers,
    )

    assert response.status_code == 201

    metric_event_id = response.json()["id"]

    # ---------------------------------------------------------
    # Request anomaly detection
    # ---------------------------------------------------------

    response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/metrics/{metric_event_id}/detect",
        headers=headers,
    )

    # ---------------------------------------------------------
    # Verify API response
    # ---------------------------------------------------------

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "anomaly"

    assert result["metric_name"] == "checkout_latency"

    assert result["current_value"] == 165

    assert result["baseline_value"] is not None

    assert result["z_score"] is not None

    assert result["robust_z_score"] is not None

    assert result["anomalous_observations"] >= 3

    assert result["detection_method"] is not None

    assert result["explanation"] is not None