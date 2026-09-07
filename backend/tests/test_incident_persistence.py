from datetime import datetime, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.correlation import (
    CorrelationLevel,
    CorrelationResult,
)
from backend.app.services.incident_formation import (
    form_incident_candidate,
)
from backend.app.services.incident_persistence import (
    persist_incident_candidate,
)


def make_correlation_result(signal_id):
    return CorrelationResult(
        related_signal_id=signal_id,
        related_signal_type="log_error",
        related_signal_name="payment_timeout",
        correlation_score=0.80,
        correlation_level=CorrelationLevel.STRONG,
        temporal_score=0.90,
        service_score=1.0,
        telemetry_score=1.0,
        deployment_score=0.0,
        time_difference_seconds=30.0,
        same_service=True,
        deployment_nearby=False,
        reasons=[
            "Signals occurred 30 seconds apart.",
            "Signals belong to the same service.",
            "Signal types have a recognized telemetry relationship.",
        ],
    )


def test_persist_incident_candidate():
    db = SessionLocal()

    try:
        user = User(
            email=f"incident-persistence-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(user)
        db.flush()

        project = Project(
            name="Incident Persistence Project",
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

        metric_event_id = uuid4()
        log_event_id = uuid4()
        detected_at = datetime.now(timezone.utc)

        correlation_result = make_correlation_result(
            log_event_id
        )

        candidate = form_incident_candidate(
            service_id=service.id,
            metric_name="checkout_latency",
            metric_value=250.0,
            detected_at=detected_at,
            metric_event_id=metric_event_id,
            correlation_results=[correlation_result],
        )

        assert candidate is not None

        incident = persist_incident_candidate(
            db=db,
            candidate=candidate,
        )

        assert incident.id is not None
        assert incident.project_id == project.id
        assert incident.title.startswith(
            "Potential incident:"
        )
        assert incident.severity == "high"
        assert incident.status == "open"

        evidence_items = (
            db.query(EvidenceItem)
            .filter(
                EvidenceItem.incident_id == incident.id
            )
            .all()
        )

        assert len(evidence_items) == 2

        evidence_source_ids = {
            evidence.source_id
            for evidence in evidence_items
        }

        assert metric_event_id in evidence_source_ids
        assert log_event_id in evidence_source_ids

    finally:
        db.rollback()
        db.close()