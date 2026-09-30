from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_user_and_service():
    email = f"telemetry-{uuid4()}@example.com"
    password = "testpassword123"

    # Register user
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    # Login
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

    # Create project
    project_response = client.post(
        "/api/projects",
        json={
            "name": "Telemetry Test Project"
        },
        headers=headers,
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # Create service
    service_response = client.post(
        f"/api/projects/{project_id}/services",
        json={
            "name": "Checkout Service"
        },
        headers=headers,
    )

    assert service_response.status_code == 201

    service_id = service_response.json()["id"]

    return headers, project_id, service_id


def test_create_and_get_log():
    headers, project_id, service_id = create_user_and_service()

    timestamp = datetime.now(timezone.utc).isoformat()

    create_response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/logs",
        json={
            "timestamp": timestamp,
            "level": "ERROR",
            "message": "Payment service timeout",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    created_log = create_response.json()

    assert created_log["service_id"] == service_id
    assert created_log["level"] == "ERROR"
    assert created_log["message"] == "Payment service timeout"

    # Retrieve logs
    get_response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/logs",
        headers=headers,
    )

    assert get_response.status_code == 200

    logs = get_response.json()

    assert len(logs) >= 1
    assert logs[0]["message"] == "Payment service timeout"


def test_create_and_get_metric():
    headers, project_id, service_id = create_user_and_service()

    timestamp = datetime.now(timezone.utc).isoformat()

    create_response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        json={
            "timestamp": timestamp,
            "name": "checkout_latency",
            "value": 842.5,
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    created_metric = create_response.json()

    assert created_metric["service_id"] == service_id
    assert created_metric["name"] == "checkout_latency"
    assert created_metric["value"] == 842.5

    # Retrieve metrics
    get_response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        headers=headers,
    )

    assert get_response.status_code == 200

    metrics = get_response.json()

    assert len(metrics) >= 1
    assert metrics[0]["name"] == "checkout_latency"


def test_create_and_get_deployment():
    headers, project_id, service_id = create_user_and_service()

    timestamp = datetime.now(timezone.utc).isoformat()

    create_response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/deployments",
        json={
            "timestamp": timestamp,
            "version": "v1.2.0",
            "description": "Payment retry logic update",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    deployment = create_response.json()

    assert deployment["service_id"] == service_id
    assert deployment["version"] == "v1.2.0"
    assert deployment["description"] == "Payment retry logic update"

    # Retrieve deployments
    get_response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/deployments",
        headers=headers,
    )

    assert get_response.status_code == 200

    deployments = get_response.json()

    assert len(deployments) >= 1
    assert deployments[0]["version"] == "v1.2.0"


def test_log_time_filter_and_limit():
    headers, project_id, service_id = create_user_and_service()

    now = datetime.now(timezone.utc)

    timestamps = [
        now - timedelta(minutes=30),
        now - timedelta(minutes=20),
        now - timedelta(minutes=10),
    ]

    for index, timestamp in enumerate(timestamps):
        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/logs",
            json={
                "timestamp": timestamp.isoformat(),
                "level": "INFO",
                "message": f"Test log {index}",
            },
            headers=headers,
        )

        assert response.status_code == 201

    # Retrieve only the most recent two logs
    response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/logs",
        params={
            "limit": 2,
        },
        headers=headers,
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 2

    # Results should be newest first
    assert logs[0]["message"] == "Test log 2"
    assert logs[1]["message"] == "Test log 1"

    # Time filtering
    start_time = (now - timedelta(minutes=15)).isoformat()

    response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/logs",
        params={
            "start_time": start_time,
        },
        headers=headers,
    )

    assert response.status_code == 200

    filtered_logs = response.json()

    assert len(filtered_logs) == 1
    assert filtered_logs[0]["message"] == "Test log 2"


def test_log_end_time_filter():
    headers, project_id, service_id = create_user_and_service()

    now = datetime.now(timezone.utc)

    timestamps = [
        now - timedelta(minutes=30),
        now - timedelta(minutes=20),
        now - timedelta(minutes=10),
    ]

    for index, timestamp in enumerate(timestamps):
        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/logs",
            json={
                "timestamp": timestamp.isoformat(),
                "level": "INFO",
                "message": f"End filter log {index}",
            },
            headers=headers,
        )

        assert response.status_code == 201

    end_time = (now - timedelta(minutes=15)).isoformat()

    response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/logs",
        params={
            "end_time": end_time,
        },
        headers=headers,
    )

    assert response.status_code == 200

    filtered_logs = response.json()

    assert len(filtered_logs) == 2
    assert filtered_logs[0]["message"] == "End filter log 1"
    assert filtered_logs[1]["message"] == "End filter log 0"


def test_metric_time_filters_and_limit():
    headers, project_id, service_id = create_user_and_service()

    now = datetime.now(timezone.utc)

    timestamps = [
        now - timedelta(minutes=30),
        now - timedelta(minutes=20),
        now - timedelta(minutes=10),
    ]

    for index, timestamp in enumerate(timestamps):
        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/metrics",
            json={
                "timestamp": timestamp.isoformat(),
                "name": "checkout_latency",
                "value": float(index + 1),
            },
            headers=headers,
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        params={
            "start_time": (
                now - timedelta(minutes=25)
            ).isoformat(),
            "end_time": (
                now - timedelta(minutes=5)
            ).isoformat(),
            "limit": 2,
        },
        headers=headers,
    )

    assert response.status_code == 200

    metrics = response.json()

    assert len(metrics) == 2
    assert metrics[0]["value"] == 3.0
    assert metrics[1]["value"] == 2.0


def test_deployment_time_filters_and_limit():
    headers, project_id, service_id = create_user_and_service()

    now = datetime.now(timezone.utc)

    timestamps = [
        now - timedelta(minutes=30),
        now - timedelta(minutes=20),
        now - timedelta(minutes=10),
    ]

    for index, timestamp in enumerate(timestamps):
        response = client.post(
            f"/api/projects/{project_id}/services/{service_id}/deployments",
            json={
                "timestamp": timestamp.isoformat(),
                "version": f"v1.{index}.0",
                "description": f"Deployment {index}",
            },
            headers=headers,
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/projects/{project_id}/services/{service_id}/deployments",
        params={
            "start_time": (
                now - timedelta(minutes=25)
            ).isoformat(),
            "end_time": (
                now - timedelta(minutes=5)
            ).isoformat(),
            "limit": 2,
        },
        headers=headers,
    )

    assert response.status_code == 200

    deployments = response.json()

    assert len(deployments) == 2
    assert deployments[0]["version"] == "v1.2.0"
    assert deployments[1]["version"] == "v1.1.0"


def test_detect_nonexistent_metric_returns_404():
    headers, project_id, service_id = create_user_and_service()

    response = client.post(
        f"/api/projects/{project_id}/services/"
        f"{service_id}/metrics/{uuid4()}/detect",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Metric event not found."


def test_process_incident_nonexistent_metric_returns_404():
    headers, project_id, service_id = create_user_and_service()

    response = client.post(
        f"/api/projects/{project_id}/services/"
        f"{service_id}/metrics/{uuid4()}/process-incident",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Metric event not found."


def test_process_metric_without_qualifying_incident():
    headers, project_id, service_id = create_user_and_service()

    timestamp = datetime.now(timezone.utc).isoformat()

    create_response = client.post(
        f"/api/projects/{project_id}/services/{service_id}/metrics",
        json={
            "timestamp": timestamp,
            "name": "checkout_latency",
            "value": 100.0,
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    metric_id = create_response.json()["id"]

    response = client.post(
        f"/api/projects/{project_id}/services/"
        f"{service_id}/metrics/{metric_id}/process-incident",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["incident_created"] is False
    assert (
        data["message"]
        == "Metric event did not produce a qualifying incident."
    )