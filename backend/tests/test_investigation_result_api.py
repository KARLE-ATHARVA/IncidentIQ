from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api.investigations import get_reasoning_engine
from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.investigation_reasoning import (
    DeterministicReasoner,
)
from backend.app.services.reasoning_engine import ReasoningEngine


client = TestClient(app)


class FailingReasoningEngine(ReasoningEngine):
    def generate(self, context):
        raise RuntimeError("Simulated AI reasoning failure.")


def create_user_project_incident_investigation():
    db = SessionLocal()

    user = User(
        email=f"investigation-result-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"Investigation Result API Project {uuid4()}",
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

    base_time = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Historical metric observations
    # ------------------------------------------------------------------

    for index in range(20):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time - timedelta(minutes=25 - index),
                name="checkout_latency",
                value=100.0 + (index % 2),
            )
        )

    # ------------------------------------------------------------------
    # Recent anomalous observations
    # ------------------------------------------------------------------

    for index in range(5):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time - timedelta(minutes=5 - index),
                name="checkout_latency",
                value=160.0 + index,
            )
        )

    current_metric = MetricEvent(
        service_id=service.id,
        timestamp=base_time,
        name="checkout_latency",
        value=180.0,
    )

    db.add(current_metric)

    # ------------------------------------------------------------------
    # Error log
    # ------------------------------------------------------------------

    db.add(
        LogEvent(
            service_id=service.id,
            timestamp=base_time + timedelta(seconds=30),
            level="ERROR",
            message="Payment provider timeout",
        )
    )

    # ------------------------------------------------------------------
    # Deployment
    # ------------------------------------------------------------------

    db.add(
        DeploymentEvent(
            service_id=service.id,
            timestamp=base_time - timedelta(seconds=60),
            version="checkout-v42",
            description="Checkout deployment",
        )
    )

    db.flush()

    # ------------------------------------------------------------------
    # Incident
    # ------------------------------------------------------------------

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status="open",
        detected_at=base_time,
    )

    db.add(incident)
    db.flush()

    # ------------------------------------------------------------------
    # Investigation
    # ------------------------------------------------------------------

    investigation = Investigation(
        incident_id=incident.id,
        status="pending",
    )

    db.add(investigation)
    db.commit()

    db.refresh(user)
    db.refresh(project)
    db.refresh(service)
    db.refresh(incident)
    db.refresh(investigation)

    return db, user, project, incident, investigation


def create_token(user_id):
    return create_access_token(str(user_id))


def investigation_url(project, incident, investigation):
    return (
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}"
    )


# ---------------------------------------------------------------------------
# Generate investigation result
# ---------------------------------------------------------------------------


def test_generate_investigation_result_requires_auth():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    try:
        response = client.post(
            f"{investigation_url(project, incident, investigation)}"
            "/generate-result"
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_generate_investigation_result_returns_result():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    # API tests should not depend on Ollama/Qwen availability.
    # DeterministicReasoner is used as the injected primary engine.
    app.dependency_overrides[get_reasoning_engine] = (
        lambda: DeterministicReasoner()
    )

    try:
        token = create_token(user.id)

        response = client.post(
            f"{investigation_url(project, incident, investigation)}"
            "/generate-result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"] is not None
        assert data["investigation_id"] == str(investigation.id)
        assert data["hypothesis"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["reasoning"]

        # The injected reasoning engine is being used as the
        # primary reasoning path, so the API should report "ai".
        assert data["reasoning_source"] == "ai"

        # Verify provenance was persisted.
        db_result = (
            db.query(InvestigationResult)
            .filter(InvestigationResult.id == data["id"])
            .first()
        )

        assert db_result is not None
        assert db_result.reasoning_source == "ai"

        assert isinstance(data["next_steps"], list)
        assert len(data["next_steps"]) > 0

        # Day 12 evaluation metadata.
        assert "evaluation" in data
        assert data["evaluation"]["is_valid"] is True
        assert data["evaluation"]["evidence_count"] > 0
        assert data["evaluation"]["supporting_evidence_count"] > 0
        assert 0.0 <= data["evaluation"]["evidence_coverage"] <= 1.0

    finally:
        app.dependency_overrides.pop(get_reasoning_engine, None)
        db.rollback()
        db.close()


def test_generate_investigation_result_uses_deterministic_fallback_when_ai_fails():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    app.dependency_overrides[get_reasoning_engine] = (
        lambda: FailingReasoningEngine()
    )

    try:
        token = create_token(user.id)

        response = client.post(
            f"{investigation_url(project, incident, investigation)}"
            "/generate-result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"] is not None
        assert data["investigation_id"] == str(investigation.id)
        assert data["hypothesis"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["reasoning"]

        # AI failed, therefore deterministic fallback must be reported.
        assert data["reasoning_source"] == "deterministic_fallback"

        # Verify fallback provenance was persisted.
        db_result = (
            db.query(InvestigationResult)
            .filter(InvestigationResult.id == data["id"])
            .first()
        )

        assert db_result is not None
        assert db_result.reasoning_source == "deterministic_fallback"

        assert isinstance(data["alternative_explanations"], list)
        assert len(data["alternative_explanations"]) > 0

        assert isinstance(data["next_steps"], list)
        assert len(data["next_steps"]) > 0

        # Evaluation must still succeed for the fallback result.
        assert "evaluation" in data
        assert data["evaluation"]["is_valid"] is True

    finally:
        app.dependency_overrides.pop(get_reasoning_engine, None)
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# Get investigation result
# ---------------------------------------------------------------------------


def test_get_investigation_result_requires_auth():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    try:
        response = client.get(
            f"{investigation_url(project, incident, investigation)}"
            "/result"
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_get_investigation_result_returns_complete_result():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    app.dependency_overrides[get_reasoning_engine] = (
        lambda: DeterministicReasoner()
    )

    try:
        token = create_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}

        generate_response = client.post(
            f"{investigation_url(project, incident, investigation)}"
            "/generate-result",
            headers=headers,
        )

        assert generate_response.status_code == 201

        response = client.get(
            f"{investigation_url(project, incident, investigation)}"
            "/result",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] is not None
        assert data["investigation_id"] == str(investigation.id)

        assert data["created_at"] is not None

        assert data["hypothesis"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["reasoning"]

        # Verify provenance survives persistence and retrieval.
        assert data["reasoning_source"] == "ai"

        assert isinstance(data["alternative_explanations"], list)
        assert len(data["alternative_explanations"]) > 0

        assert isinstance(data["next_steps"], list)
        assert len(data["next_steps"]) > 0

        assert isinstance(data["supporting_evidence"], list)
        assert len(data["supporting_evidence"]) >= 3

        for evidence in data["supporting_evidence"]:
            assert evidence["id"]
            assert evidence["source_type"]
            assert evidence["source_id"]
            assert evidence["title"]
            assert evidence["description"]
            assert evidence["collected_at"]

    finally:
        app.dependency_overrides.pop(get_reasoning_engine, None)
        db.rollback()
        db.close()


def test_get_investigation_result_returns_404_when_result_does_not_exist():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    try:
        token = create_token(user.id)

        response = client.get(
            f"{investigation_url(project, incident, investigation)}"
            "/result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Investigation result not found."
        )

    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# Authorization / project isolation
# ---------------------------------------------------------------------------


def test_investigation_result_cannot_be_accessed_from_wrong_project():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    try:
        other_user = User(
            email=f"other-user-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(other_user)
        db.flush()

        other_project = Project(
            name=f"Other Project {uuid4()}",
            owner_id=other_user.id,
        )

        db.add(other_project)
        db.commit()

        db.refresh(other_project)

        token = create_token(other_user.id)

        response = client.get(
            f"/api/projects/{other_project.id}/incidents/"
            f"{incident.id}/investigations/{investigation.id}/result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in (403, 404)

    finally:
        db.rollback()
        db.close()


def test_generate_investigation_result_cannot_be_created_from_wrong_project():
    db, user, project, incident, investigation = (
        create_user_project_incident_investigation()
    )

    try:
        other_user = User(
            email=f"other-generate-user-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(other_user)
        db.flush()

        other_project = Project(
            name=f"Other Generate Project {uuid4()}",
            owner_id=other_user.id,
        )

        db.add(other_project)
        db.commit()

        db.refresh(other_project)

        token = create_token(other_user.id)

        response = client.post(
            f"/api/projects/{other_project.id}/incidents/"
            f"{incident.id}/investigations/{investigation.id}/generate-result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in (403, 404)

    finally:
        db.rollback()
        db.close()