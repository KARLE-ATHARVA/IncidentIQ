from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.services.timeline import (
    TimelineConfig,
    calculate_timeline_window,
    normalize_deployment_event,
    normalize_log_event,
    normalize_metric_event,
)
from fastapi.testclient import TestClient

from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.models.metric_event import MetricEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.core.security import create_access_token

from backend.app.models.project import Project
client = TestClient(app)


def test_calculate_timeline_window_defaults_to_ten_minutes():
    detected_at = datetime(
        2026,
        9,
        9,
        0,
        7,
        10,
        tzinfo=timezone.utc,
    )

    start_time, end_time = calculate_timeline_window(
        detected_at=detected_at,
    )

    assert start_time == detected_at - timedelta(minutes=10)
    assert end_time == detected_at + timedelta(minutes=10)


def test_calculate_timeline_window_supports_custom_window():
    detected_at = datetime(
        2026,
        9,
        9,
        0,
        7,
        10,
        tzinfo=timezone.utc,
    )

    config = TimelineConfig(window_minutes=30)

    start_time, end_time = calculate_timeline_window(
        detected_at=detected_at,
        config=config,
    )

    assert start_time == detected_at - timedelta(minutes=30)
    assert end_time == detected_at + timedelta(minutes=30)


def test_timeline_config_rejects_non_positive_window():
    with pytest.raises(ValueError):
        TimelineConfig(window_minutes=0)

    with pytest.raises(ValueError):
        TimelineConfig(window_minutes=-10)

def test_normalize_metric_event():
    service_id = uuid4()
    metric_id = uuid4()

    timestamp = datetime(
        2026,
        9,
        9,
        0,
        5,
        10,
        tzinfo=timezone.utc,
    )

    event = MetricEvent(
        id=metric_id,
        service_id=service_id,
        timestamp=timestamp,
        name="checkout_latency",
        value=175.0,
    )

    timeline_event = normalize_metric_event(event)

    assert timeline_event.id == metric_id
    assert timeline_event.source_id == metric_id
    assert timeline_event.timestamp == timestamp
    assert timeline_event.event_type == "metric"
    assert timeline_event.service_id == service_id
    assert timeline_event.title == "checkout_latency"
    assert timeline_event.description == "checkout_latency = 175.0"
    assert timeline_event.severity is None
    assert timeline_event.metadata["metric_name"] == "checkout_latency"
    assert timeline_event.metadata["value"] == 175.0

def test_normalize_log_event():
    service_id = uuid4()
    log_id = uuid4()

    timestamp = datetime(
        2026,
        9,
        9,
        0,
        6,
        40,
        tzinfo=timezone.utc,
    )

    event = LogEvent(
        id=log_id,
        service_id=service_id,
        timestamp=timestamp,
        level="ERROR",
        message="Checkout requests are timing out.",
    )

    timeline_event = normalize_log_event(event)

    assert timeline_event.id == log_id
    assert timeline_event.source_id == log_id
    assert timeline_event.timestamp == timestamp
    assert timeline_event.event_type == "log"
    assert timeline_event.service_id == service_id
    assert timeline_event.title == "ERROR log"
    assert timeline_event.description == (
        "Checkout requests are timing out."
    )
    assert timeline_event.severity == "ERROR"
    assert timeline_event.metadata["level"] == "ERROR"
    assert timeline_event.metadata["message"] == (
        "Checkout requests are timing out."
    )

def test_normalize_deployment_event():
    service_id = uuid4()
    deployment_id = uuid4()

    timestamp = datetime(
        2026,
        9,
        9,
        0,
        5,
        10,
        tzinfo=timezone.utc,
    )

    event = DeploymentEvent(
        id=deployment_id,
        service_id=service_id,
        timestamp=timestamp,
        version="v2.4.0",
        description="Deployed checkout payment integration changes.",
    )

    timeline_event = normalize_deployment_event(event)

    assert timeline_event.id == deployment_id
    assert timeline_event.source_id == deployment_id
    assert timeline_event.timestamp == timestamp
    assert timeline_event.event_type == "deployment"
    assert timeline_event.service_id == service_id
    assert timeline_event.title == "Deployment v2.4.0"
    assert timeline_event.description == (
        "Deployed checkout payment integration changes."
    )
    assert timeline_event.severity is None
    assert timeline_event.metadata["version"] == "v2.4.0"

def test_build_timeline_events_sorts_all_event_types():
    from backend.app.services.timeline import build_timeline_events

    service_id = uuid4()

    metric = MetricEvent(
        id=uuid4(),
        service_id=service_id,
        timestamp=datetime(
            2026,
            9,
            9,
            0,
            7,
            0,
            tzinfo=timezone.utc,
        ),
        name="checkout_latency",
        value=175.0,
    )

    log = LogEvent(
        id=uuid4(),
        service_id=service_id,
        timestamp=datetime(
            2026,
            9,
            9,
            0,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        level="ERROR",
        message="Checkout timeout.",
    )

    deployment = DeploymentEvent(
        id=uuid4(),
        service_id=service_id,
        timestamp=datetime(
            2026,
            9,
            9,
            0,
            5,
            0,
            tzinfo=timezone.utc,
        ),
        version="v2.4.0",
        description="Payment integration deployment.",
    )

    events = build_timeline_events(
        metrics=[metric],
        logs=[log],
        deployments=[deployment],
    )

    assert len(events) == 3

    assert events[0].event_type == "deployment"
    assert events[1].event_type == "log"
    assert events[2].event_type == "metric"

    assert events[0].timestamp < events[1].timestamp
    assert events[1].timestamp < events[2].timestamp

def create_timeline_test_data():
    db = SessionLocal()

    user = User(
        email=f"timeline-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"Timeline Project {uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.flush()

    service = Service(
        name="Checkout Service",
        project_id=project.id,
    )

    db.add(service)
    db.flush()

    detected_at = datetime(
        2026,
        9,
        9,
        0,
        7,
        10,
        tzinfo=timezone.utc,
    )

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Latency increased significantly.",
        severity="high",
        status="open",
        detected_at=detected_at,
    )

    db.add(incident)
    db.commit()

    db.refresh(user)
    db.refresh(project)
    db.refresh(service)
    db.refresh(incident)

    return db, user, project, service, incident

def test_timeline_includes_events_inside_window_and_excludes_outside():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        detected_at = incident.detected_at

        inside_metric = MetricEvent(
            service_id=service.id,
            timestamp=detected_at - timedelta(minutes=5),
            name="checkout_latency",
            value=150.0,
        )

        boundary_metric = MetricEvent(
            service_id=service.id,
            timestamp=detected_at - timedelta(minutes=10),
            name="checkout_latency",
            value=120.0,
        )

        outside_metric = MetricEvent(
            service_id=service.id,
            timestamp=detected_at - timedelta(minutes=11),
            name="checkout_latency",
            value=110.0,
        )

        inside_log = LogEvent(
            service_id=service.id,
            timestamp=detected_at + timedelta(minutes=2),
            level="ERROR",
            message="Checkout timeout.",
        )

        inside_deployment = DeploymentEvent(
            service_id=service.id,
            timestamp=detected_at - timedelta(minutes=2),
            version="v2.4.0",
            description="Payment integration deployment.",
        )

        db.add_all(
            [
                inside_metric,
                boundary_metric,
                outside_metric,
                inside_log,
                inside_deployment,
            ]
        )

        db.commit()

        token = create_access_token(str(user.id))

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["incident_id"] == str(incident.id)

        event_source_ids = {
            event["source_id"]
            for event in data["events"]
        }

        assert str(inside_metric.id) in event_source_ids
        assert str(boundary_metric.id) in event_source_ids
        assert str(inside_log.id) in event_source_ids
        assert str(inside_deployment.id) in event_source_ids

        assert str(outside_metric.id) not in event_source_ids

    finally:
        db.rollback()
        db.close()

def test_timeline_returns_events_in_chronological_order():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        detected_at = incident.detected_at

        metric = MetricEvent(
            service_id=service.id,
            timestamp=detected_at + timedelta(minutes=3),
            name="checkout_latency",
            value=175.0,
        )

        log = LogEvent(
            service_id=service.id,
            timestamp=detected_at + timedelta(minutes=1),
            level="ERROR",
            message="Checkout timeout.",
        )

        deployment = DeploymentEvent(
            service_id=service.id,
            timestamp=detected_at - timedelta(minutes=2),
            version="v2.4.0",
            description="Payment integration deployment.",
        )

        db.add_all([metric, log, deployment])
        db.commit()

        token = create_access_token(str(user.id))

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        events = response.json()["events"]

        # All three telemetry types should be present.
        event_types = {event["event_type"] for event in events}

        assert "metric" in event_types
        assert "log" in event_types
        assert "deployment" in event_types

        # Timeline must be chronological.
        timestamps = [
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            for event in events
        ]

        assert timestamps == sorted(timestamps)

    finally:
        db.rollback()
        db.close()

def test_timeline_requires_authentication():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline"
        )

        assert response.status_code == 401

    finally:
        db.rollback()
        db.close()


def test_timeline_rejects_other_users_project():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        other_user = User(
            email=f"other-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        token = create_access_token(str(other_user.id))

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    finally:
        db.rollback()
        db.close()


def test_timeline_returns_empty_events_when_no_telemetry_exists():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        token = create_access_token(str(user.id))

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["incident_id"] == str(incident.id)
        assert data["events"] == []

    finally:
        db.rollback()
        db.close()


def test_timeline_does_not_include_events_from_another_project():
    db, user, project, service, incident = create_timeline_test_data()

    try:
        other_project = Project(
            name=f"Other Project {uuid4()}",
            owner_id=user.id,
        )
        db.add(other_project)
        db.flush()

        other_service = Service(
            name="Other Service",
            project_id=other_project.id,
        )
        db.add(other_service)
        db.commit()
        db.refresh(other_service)

        unrelated_metric = MetricEvent(
            service_id=other_service.id,
            timestamp=incident.detected_at,
            name="unrelated_metric",
            value=999.0,
        )

        db.add(unrelated_metric)
        db.commit()

        token = create_access_token(str(user.id))

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/timeline",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        event_source_ids = {
            event["source_id"]
            for event in response.json()["events"]
        }

        assert str(unrelated_metric.id) not in event_source_ids

    finally:
        db.rollback()
        db.close()