from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.metric_event import MetricEvent
from backend.app.services.detection import (
    DetectionConfig,
    DetectionStatus,
)
from backend.app.services.detection_integration import (
    detect_metric_event_anomaly,
)


client = TestClient(app)


def create_user_project_and_service():
    """
    Create the authenticated test environment:
    user -> project -> service.
    """

    email = f"detection-{uuid4()}@example.com"
    password = "testpassword123"

    # ---------------------------------------------------------
    # Register user
    # ---------------------------------------------------------

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    # ---------------------------------------------------------
    # Login
    # ---------------------------------------------------------

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # ---------------------------------------------------------
    # Create project
    # ---------------------------------------------------------

    project_response = client.post(
        "/api/projects",
        json={
            "name": "Detection Integration Test Project",
        },
        headers=headers,
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # ---------------------------------------------------------
    # Create service
    # ---------------------------------------------------------

    service_response = client.post(
        f"/api/projects/{project_id}/services",
        json={
            "name": "Checkout Detection Service",
        },
        headers=headers,
    )

    assert service_response.status_code == 201

    service_id = service_response.json()["id"]

    return headers, project_id, service_id


def test_detection_integration_with_postgresql():
    """
    Verify that the detection integration layer can:

    PostgreSQL
        ↓
    metric_events
        ↓
    detection_integration.py
        ↓
    detection.py
        ↓
    AnomalyDetectionResult
    """

    headers, project_id, service_id = (
        create_user_project_and_service()
    )

    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # 1. Create 20 historical observations
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
    # 2. Create 5 recent anomalous observations
    # ---------------------------------------------------------

    recent_values = [165, 165, 165, 165, 165]

    for index, value in enumerate(recent_values):
        timestamp = now - timedelta(
            minutes=5 - index
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
    # 3. Create the current observation
    # ---------------------------------------------------------

    current_timestamp = now

    current_response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        json={
            "timestamp": current_timestamp.isoformat(),
            "name": "checkout_latency",
            "value": 165,
        },
        headers=headers,
    )

    assert current_response.status_code == 201

    current_metric = current_response.json()

    current_metric_id = current_metric["id"]

    # ---------------------------------------------------------
    # 4. Run the integration service using PostgreSQL
    # ---------------------------------------------------------

    db = SessionLocal()

    try:
        result = detect_metric_event_anomaly(
            db=db,
            metric_event_id=current_metric_id,
            config=DetectionConfig(
                minimum_observations=10,
                persistence_window=3,
            ),
        )

    finally:
        db.close()

    # ---------------------------------------------------------
    # 5. Verify the detection result
    # ---------------------------------------------------------

    assert result.status == DetectionStatus.ANOMALY

    assert result.metric_name == "checkout_latency"

    assert result.current_value == 165

    assert result.baseline_value is not None

    assert result.z_score is not None

    assert result.robust_z_score is not None

    assert result.anomalous_observations >= 3

    assert result.detection_method is not None

    assert result.explanation is not None