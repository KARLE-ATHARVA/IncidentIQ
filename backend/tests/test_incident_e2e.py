from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api.investigations import get_reasoning_engine
from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)
from backend.app.services.investigation_reasoning import (
    DeterministicReasoner,
)


client = TestClient(app)


def create_e2e_environment():
    db = SessionLocal()

    user = User(
        email=f"incident-e2e-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"IncidentIQ E2E Project {uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.flush()

    service = Service(
        name="checkout",
        project_id=project.id,
    )

    db.add(service)
    db.flush()

    return db, user, project, service


def create_incident_telemetry(db, service):
    base_time = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # Historical normal metrics
    # ---------------------------------------------------------

    for index in range(20):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time - timedelta(minutes=25 - index),
                name="checkout_latency",
                value=100.0 + (index % 2),
            )
        )

    # ---------------------------------------------------------
    # Recent anomalous observations
    # ---------------------------------------------------------

    for index in range(5):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time - timedelta(minutes=5 - index),
                name="checkout_latency",
                value=160.0 + index,
            )
        )

    db.flush()

    # ---------------------------------------------------------
    # Current anomalous metric
    # ---------------------------------------------------------

    current_metric = MetricEvent(
        service_id=service.id,
        timestamp=base_time,
        name="checkout_latency",
        value=180.0,
    )

    db.add(current_metric)

    # ---------------------------------------------------------
    # Correlated ERROR log
    # ---------------------------------------------------------

    error_log = LogEvent(
        service_id=service.id,
        timestamp=base_time + timedelta(seconds=30),
        level="ERROR",
        message="Payment provider timeout",
    )

    db.add(error_log)

    # ---------------------------------------------------------
    # Correlated deployment
    # ---------------------------------------------------------

    deployment = DeploymentEvent(
        service_id=service.id,
        timestamp=base_time - timedelta(seconds=60),
        version="checkout-v42",
        description="Checkout deployment",
    )

    db.add(deployment)

    db.commit()

    db.refresh(current_metric)
    db.refresh(error_log)
    db.refresh(deployment)

    return current_metric, error_log, deployment


def create_token(user_id):
    return create_access_token(str(user_id))


def test_full_incident_investigation_e2e():
    """
    Product-level end-to-end test.

    Verifies:

        telemetry
            -> detection/correlation
            -> incident
            -> timeline
            -> evidence
            -> investigation
            -> investigation result
            -> incident resolution
    """

    db, user, project, service = create_e2e_environment()

    app.dependency_overrides[get_reasoning_engine] = (
        lambda: DeterministicReasoner()
    )

    try:
        current_metric, error_log, deployment = create_incident_telemetry(
            db=db,
            service=service,
        )

        # -----------------------------------------------------
        # 1. Run the real incident pipeline
        # -----------------------------------------------------

        incident = process_metric_event_for_incident(
            db=db,
            metric_event_id=current_metric.id,
        )

        assert incident is not None
        assert incident.project_id == project.id
        assert incident.status == "open"
        assert incident.severity in {
            "medium",
            "high",
            "critical",
        }

        # -----------------------------------------------------
        # 2. Verify incident persisted
        # -----------------------------------------------------

        persisted_incident = (
            db.query(Incident)
            .filter(Incident.id == incident.id)
            .first()
        )

        assert persisted_incident is not None
        assert persisted_incident.id == incident.id

        # -----------------------------------------------------
        # 3. Verify evidence
        # -----------------------------------------------------

        evidence_items = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.incident_id == incident.id)
            .all()
        )

        assert len(evidence_items) >= 3

        evidence_source_ids = {
            evidence.source_id
            for evidence in evidence_items
        }

        assert current_metric.id in evidence_source_ids
        assert error_log.id in evidence_source_ids
        assert deployment.id in evidence_source_ids

        # -----------------------------------------------------
        # 4. Verify timeline through API
        # -----------------------------------------------------

        token = create_token(user.id)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        timeline_response = client.get(
            f"/api/projects/{project.id}"
            f"/incidents/{incident.id}/timeline",
            headers=headers,
        )

        assert timeline_response.status_code == 200

        timeline = timeline_response.json()

        assert timeline["incident_id"] == str(incident.id)
        assert len(timeline["events"]) >= 3

        timeline_source_ids = {
            event["source_id"]
            for event in timeline["events"]
        }

        assert str(current_metric.id) in timeline_source_ids
        assert str(error_log.id) in timeline_source_ids
        assert str(deployment.id) in timeline_source_ids

        # -----------------------------------------------------
        # 5. Create investigation
        # -----------------------------------------------------

        investigation_response = client.post(
            f"/api/projects/{project.id}"
            f"/incidents/{incident.id}/investigations",
            headers=headers,
        )

        assert investigation_response.status_code in (200, 201)

        investigation_data = investigation_response.json()

        investigation_id = investigation_data["id"]

        investigation = (
            db.query(Investigation)
            .filter(Investigation.id == investigation_id)
            .first()
        )

        assert investigation is not None
        assert investigation.status == "pending"

        # -----------------------------------------------------
        # 6. Generate investigation result
        # -----------------------------------------------------

        result_response = client.post(
            f"/api/projects/{project.id}"
            f"/incidents/{incident.id}"
            f"/investigations/{investigation_id}/generate-result",
            headers=headers,
        )

        assert result_response.status_code == 201

        result_data = result_response.json()

        assert result_data["id"] is not None
        assert result_data["investigation_id"] == str(
            investigation_id
        )

        assert result_data["hypothesis"]
        assert 0.0 <= result_data["confidence"] <= 1.0
        assert result_data["reasoning"]

        assert result_data["reasoning_source"] == "ai"

        assert len(result_data["supporting_evidence"]) >= 1
        assert len(result_data["alternative_explanations"]) >= 1
        assert len(result_data["next_steps"]) >= 1

        # -----------------------------------------------------
        # 7. Verify persisted investigation result
        # -----------------------------------------------------

        persisted_result = (
            db.query(InvestigationResult)
            .filter(
                InvestigationResult.id == result_data["id"]
            )
            .first()
        )

        assert persisted_result is not None
        assert (
            persisted_result.investigation_id
            == investigation.id
        )

        # -----------------------------------------------------
        # 8. Verify investigation completed
        # -----------------------------------------------------

        db.refresh(investigation)

        assert investigation.status == "completed"
        assert investigation.completed_at is not None

        # -----------------------------------------------------
        # 9. Resolve incident
        # -----------------------------------------------------

        resolve_response = client.post(
            f"/api/projects/{project.id}"
            f"/incidents/{incident.id}/resolve",
            headers=headers,
        )

        assert resolve_response.status_code == 200

        resolved_data = resolve_response.json()

        assert resolved_data["id"] == str(incident.id)
        assert resolved_data["status"] == "resolved"
        assert resolved_data["resolved_at"] is not None

        # -----------------------------------------------------
        # 10. Verify final database state
        # -----------------------------------------------------

        db.refresh(incident)

        assert incident.status == "resolved"
        assert incident.resolved_at is not None

    finally:
        app.dependency_overrides.pop(
            get_reasoning_engine,
            None,
        )

        db.rollback()
        db.close()


def test_incident_pipeline_rejects_insufficient_telemetry():
    """
    Failure-path test.

    A service with insufficient historical observations should
    not produce a qualifying incident.
    """

    db, user, project, service = create_e2e_environment()

    try:
        base_time = datetime.now(timezone.utc)

        # Only three observations: below the detector's
        # minimum historical observation requirement.
        for index in range(3):
            db.add(
                MetricEvent(
                    service_id=service.id,
                    timestamp=base_time - timedelta(minutes=3 - index),
                    name="checkout_latency",
                    value=180.0,
                )
            )

        db.flush()

        current_metric = MetricEvent(
            service_id=service.id,
            timestamp=base_time,
            name="checkout_latency",
            value=200.0,
        )

        db.add(current_metric)
        db.commit()
        db.refresh(current_metric)

        incident = process_metric_event_for_incident(
            db=db,
            metric_event_id=current_metric.id,
        )

        assert incident is None

        persisted_incidents = (
            db.query(Incident)
            .filter(
                Incident.project_id == project.id
            )
            .all()
        )

        assert persisted_incidents == []

    finally:
        db.rollback()
        db.close()