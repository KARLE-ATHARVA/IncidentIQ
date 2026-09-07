from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)


def test_full_metric_to_incident_pipeline():
    db = SessionLocal()

    try:
        user = User(
            email=f"pipeline-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(user)
        db.flush()

        project = Project(
            name="Pipeline Test Project",
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

        # -----------------------------------------------------
        # Historical baseline
        # -----------------------------------------------------

        for index in range(20):
            event = MetricEvent(
                service_id=service.id,
                timestamp=base_time
                - timedelta(minutes=20 - index),
                name="checkout_latency",
                value=100.0 + (index % 2),
            )

            db.add(event)

        # -----------------------------------------------------
        # Recent anomalous observations
        # -----------------------------------------------------

        for index in range(5):
            event = MetricEvent(
                service_id=service.id,
                timestamp=base_time
                - timedelta(minutes=5 - index),
                name="checkout_latency",
                value=160.0 + index,
            )

            db.add(event)

        db.flush()

        # -----------------------------------------------------
        # Current anomalous metric
        # -----------------------------------------------------

        current_metric = MetricEvent(
            service_id=service.id,
            timestamp=base_time,
            name="checkout_latency",
            value=180.0,
        )

        db.add(current_metric)

        # -----------------------------------------------------
        # Correlated error log
        # -----------------------------------------------------

        error_log = LogEvent(
            service_id=service.id,
            timestamp=base_time + timedelta(seconds=30),
            level="ERROR",
            message="Payment provider timeout",
        )

        db.add(error_log)

        # -----------------------------------------------------
        # Correlated deployment
        # -----------------------------------------------------

        deployment = DeploymentEvent(
            service_id=service.id,
            timestamp=base_time - timedelta(seconds=60),
            version="checkout-v42",
            description="Checkout deployment",
        )

        db.add(deployment)

        db.commit()

        # -----------------------------------------------------
        # Run complete pipeline
        # -----------------------------------------------------

        incident = process_metric_event_for_incident(
            db=db,
            metric_event_id=current_metric.id,
        )

        # -----------------------------------------------------
        # Verify incident
        # -----------------------------------------------------

        assert incident is not None

        assert incident.project_id == project.id
        assert incident.status == "open"

        assert incident.severity in {
            "medium",
            "high",
            "critical",
        }

        assert "checkout_latency" in incident.title

        # -----------------------------------------------------
        # Verify persisted evidence
        # -----------------------------------------------------

        evidence_items = (
            db.query(EvidenceItem)
            .filter(
                EvidenceItem.incident_id == incident.id
            )
            .all()
        )

        assert len(evidence_items) >= 3

        evidence_ids = {
            evidence.source_id
            for evidence in evidence_items
        }

        assert current_metric.id in evidence_ids
        assert error_log.id in evidence_ids
        assert deployment.id in evidence_ids

        # -----------------------------------------------------
        # Verify incident exists in database
        # -----------------------------------------------------

        persisted_incident = (
            db.query(Incident)
            .filter(
                Incident.id == incident.id
            )
            .first()
        )

        assert persisted_incident is not None
        assert persisted_incident.id == incident.id

    finally:
        db.rollback()
        db.close()