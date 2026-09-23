from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User


client = TestClient(app)


def utc_now():
    return datetime.now(timezone.utc)


def create_project_and_incident(db_session):
    user = User(
        email=f"evidence-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db_session.add(user)
    db_session.flush()

    project = Project(
        id=uuid4(),
        name=f"Evidence API Project {uuid4()}",
        owner_id=user.id,
    )
    db_session.add(project)
    db_session.flush()

    incident = Incident(
        id=uuid4(),
        project_id=project.id,
        title="Evidence API test incident",
        description="Incident used for evidence API tests.",
        severity="high",
        status="open",
        detected_at=utc_now(),
    )
    db_session.add(incident)
    db_session.commit()

    return user, project, incident


def create_service(db_session, project_id):
    service = Service(
        id=uuid4(),
        name=f"checkout-{uuid4()}",
        project_id=project_id,
    )
    db_session.add(service)
    db_session.flush()

    return service


def create_metric_evidence(
    db_session,
    incident,
    service,
):
    metric = MetricEvent(
        id=uuid4(),
        service_id=service.id,
        timestamp=utc_now(),
        name="checkout_latency",
        value=175.0,
    )
    db_session.add(metric)
    db_session.flush()

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="metric",
        source_id=metric.id,
        title="Checkout latency anomaly",
        description="Checkout latency exceeded the normal baseline.",
        collected_at=metric.timestamp,
    )
    db_session.add(evidence)
    db_session.commit()

    return metric, evidence


def create_log_evidence(
    db_session,
    incident,
    service,
):
    log = LogEvent(
        id=uuid4(),
        service_id=service.id,
        timestamp=utc_now(),
        level="ERROR",
        message="Payment provider request failed.",
    )
    db_session.add(log)
    db_session.flush()

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="log",
        source_id=log.id,
        title="Payment provider error",
        description="Payment provider request returned an error.",
        collected_at=log.timestamp,
    )
    db_session.add(evidence)
    db_session.commit()

    return log, evidence


def create_deployment_evidence(
    db_session,
    incident,
    service,
):
    deployment = DeploymentEvent(
        id=uuid4(),
        service_id=service.id,
        timestamp=utc_now(),
        version="v2.4.0",
        description="Checkout service deployment.",
    )
    db_session.add(deployment)
    db_session.flush()

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="deployment",
        source_id=deployment.id,
        title="Recent checkout deployment",
        description="Checkout service was recently deployed.",
        collected_at=deployment.timestamp,
    )
    db_session.add(evidence)
    db_session.commit()

    return deployment, evidence


def test_get_metric_evidence(
    db_session,
    auth_headers,
):
    user, project, incident = create_project_and_incident(
        db_session
    )
    service = create_service(
        db_session,
        project.id,
    )

    metric, evidence = create_metric_evidence(
        db_session,
        incident,
        service,
    )

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{incident.id}/evidence/{evidence.id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evidence_id"] == str(evidence.id)
    assert data["incident_id"] == str(incident.id)
    assert data["source_type"] == "metric"
    assert data["source_id"] == str(metric.id)
    assert data["service_id"] == str(service.id)
    assert data["details"]["metric_name"] == "checkout_latency"
    assert data["details"]["value"] == 175.0


def test_get_log_evidence(
    db_session,
    auth_headers,
):
    user, project, incident = create_project_and_incident(
        db_session
    )
    service = create_service(
        db_session,
        project.id,
    )

    log, evidence = create_log_evidence(
        db_session,
        incident,
        service,
    )

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{incident.id}/evidence/{evidence.id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evidence_id"] == str(evidence.id)
    assert data["source_type"] == "log"
    assert data["source_id"] == str(log.id)
    assert data["service_id"] == str(service.id)
    assert data["details"]["level"] == "ERROR"
    assert data["details"]["message"] == (
        "Payment provider request failed."
    )


def test_get_deployment_evidence(
    db_session,
    auth_headers,
):
    user, project, incident = create_project_and_incident(
        db_session
    )
    service = create_service(
        db_session,
        project.id,
    )

    deployment, evidence = create_deployment_evidence(
        db_session,
        incident,
        service,
    )

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{incident.id}/evidence/{evidence.id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evidence_id"] == str(evidence.id)
    assert data["source_type"] == "deployment"
    assert data["source_id"] == str(deployment.id)
    assert data["service_id"] == str(service.id)
    assert data["details"]["version"] == "v2.4.0"
    assert data["details"]["deployment_description"] == (
        "Checkout service deployment."
    )


def test_get_nonexistent_evidence_returns_404(
    db_session,
    auth_headers,
):
    user, project, incident = create_project_and_incident(
        db_session
    )

    nonexistent_evidence_id = uuid4()

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{incident.id}/evidence/{nonexistent_evidence_id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence not found."


def test_get_evidence_from_another_incident_returns_404(
    db_session,
    auth_headers,
):
    user, project, incident_one = create_project_and_incident(
        db_session
    )

    service = create_service(
        db_session,
        project.id,
    )

    _, evidence = create_metric_evidence(
        db_session,
        incident_one,
        service,
    )

    incident_two = Incident(
        id=uuid4(),
        project_id=project.id,
        title="Second incident",
        description="Another incident.",
        severity="medium",
        status="open",
        detected_at=utc_now(),
    )
    db_session.add(incident_two)
    db_session.commit()

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{incident_two.id}/evidence/{evidence.id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence not found."


def test_get_evidence_from_nonexistent_incident_returns_404(
    db_session,
    auth_headers,
):
    user, project, _ = create_project_and_incident(
        db_session
    )

    response = client.get(
        f"/api/projects/{project.id}/incidents/"
        f"{uuid4()}/evidence/{uuid4()}",
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found."