from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.evidence_inspection import (
    inspect_evidence,
)


def utc_now():
    return datetime.now(timezone.utc)


def create_incident(db_session):
    user = User(
        id=uuid4(),
        email=f"evidence-test-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    project = Project(
        id=uuid4(),
        name=f"Evidence Test Project {uuid4()}",
        owner_id=user.id,
    )

    db_session.add(project)
    db_session.flush()

    service = Service(
        id=uuid4(),
        name=f"Evidence Test Service {uuid4()}",
        project_id=project.id,
    )
    db_session.add(service)
    db_session.flush()

    incident = Incident(
        id=uuid4(),
        project_id=project.id,
        title="Evidence inspection test incident",
        description="Incident used for evidence inspection tests.",
        severity="high",
        status="OPEN",
        detected_at=utc_now(),
    )

    db_session.add(incident)
    db_session.flush()

    return incident, service


def test_inspect_metric_evidence(db_session):
    incident, service = create_incident(db_session)

    service_id = service.id
    metric_id = uuid4()

    metric = MetricEvent(
        id=metric_id,
        service_id=service_id,
        timestamp=utc_now(),
        name="checkout_latency",
        value=175.0,
    )

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="metric",
        source_id=metric_id,
        title="Checkout latency anomaly",
        description="Checkout latency increased significantly.",
        collected_at=utc_now(),
    )

    db_session.add(metric)
    db_session.add(evidence)
    db_session.commit()

    inspection = inspect_evidence(
        db=db_session,
        evidence=evidence,
    )

    assert inspection.evidence_id == evidence.id
    assert inspection.incident_id == incident.id
    assert inspection.source_type == "metric"
    assert inspection.source_id == metric_id
    assert inspection.service_id == service_id
    assert inspection.timestamp == metric.timestamp

    assert inspection.details["metric_name"] == "checkout_latency"
    assert inspection.details["value"] == 175.0


def test_inspect_log_evidence(db_session):
    incident, service = create_incident(db_session)

    service_id = service.id
    log_id = uuid4()

    log = LogEvent(
        id=log_id,
        service_id=service_id,
        timestamp=utc_now(),
        level="ERROR",
        message="Payment provider timeout.",
    )

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="log",
        source_id=log_id,
        title="Payment provider error",
        description="Payment provider returned an error.",
        collected_at=utc_now(),
    )

    db_session.add(log)
    db_session.add(evidence)
    db_session.commit()

    inspection = inspect_evidence(
        db=db_session,
        evidence=evidence,
    )

    assert inspection.evidence_id == evidence.id
    assert inspection.incident_id == incident.id
    assert inspection.source_type == "log"
    assert inspection.source_id == log_id
    assert inspection.service_id == service_id
    assert inspection.timestamp == log.timestamp

    assert inspection.details["level"] == "ERROR"
    assert inspection.details["message"] == "Payment provider timeout."


def test_inspect_deployment_evidence(db_session):
    incident, service = create_incident(db_session)

    service_id = service.id
    deployment_id = uuid4()

    deployment = DeploymentEvent(
        id=deployment_id,
        service_id=service_id,
        timestamp=utc_now(),
        version="v2.4.0",
        description="Checkout service deployment.",
    )

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="deployment",
        source_id=deployment_id,
        title="Recent deployment",
        description="A deployment occurred near the incident.",
        collected_at=utc_now(),
    )

    db_session.add(deployment)
    db_session.add(evidence)
    db_session.commit()

    inspection = inspect_evidence(
        db=db_session,
        evidence=evidence,
    )

    assert inspection.evidence_id == evidence.id
    assert inspection.incident_id == incident.id
    assert inspection.source_type == "deployment"
    assert inspection.source_id == deployment_id
    assert inspection.service_id == service_id
    assert inspection.timestamp == deployment.timestamp

    assert inspection.details["version"] == "v2.4.0"
    assert (
        inspection.details["deployment_description"]
        == "Checkout service deployment."
    )


def test_inspect_missing_metric_source_raises_error(db_session):
    incident, _ = create_incident(db_session)

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="metric",
        source_id=uuid4(),
        title="Missing metric",
        description="The original metric no longer exists.",
        collected_at=utc_now(),
    )

    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="Metric source for evidence was not found",
    ):
        inspect_evidence(
            db=db_session,
            evidence=evidence,
        )


def test_inspect_missing_log_source_raises_error(db_session):
    incident, _ = create_incident(db_session)

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="log",
        source_id=uuid4(),
        title="Missing log",
        description="The original log no longer exists.",
        collected_at=utc_now(),
    )

    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="Log source for evidence was not found",
    ):
        inspect_evidence(
            db=db_session,
            evidence=evidence,
        )


def test_inspect_missing_deployment_source_raises_error(db_session):
    incident, _ = create_incident(db_session)

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="deployment",
        source_id=uuid4(),
        title="Missing deployment",
        description="The original deployment no longer exists.",
        collected_at=utc_now(),
    )

    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="Deployment source for evidence was not found",
    ):
        inspect_evidence(
            db=db_session,
            evidence=evidence,
        )


def test_unsupported_evidence_source_type_raises_error(db_session):
    incident, _ = create_incident(db_session)

    evidence = EvidenceItem(
        id=uuid4(),
        incident_id=incident.id,
        source_type="unknown_source",
        source_id=uuid4(),
        title="Unsupported evidence",
        description="Unsupported evidence source.",
        collected_at=utc_now(),
    )

    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(
        ValueError,
        match="Unsupported evidence source type",
    ):
        inspect_evidence(
            db=db_session,
            evidence=evidence,
        )