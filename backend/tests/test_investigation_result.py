from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.app.db.database import SessionLocal
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.investigation_result_evidence import (
    InvestigationResultEvidence,
)
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)
from backend.app.services.investigation_context import (
    InvestigationHypothesis,
    InvestigationResultContext,
)
from backend.app.services.investigation_result import (
    persist_investigation_result,
)


def create_test_incident(db):
    user = User(
        email=f"result-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        name="Investigation Result Test Project",
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

    for index in range(20):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time
                - timedelta(minutes=25 - index),
                name="checkout_latency",
                value=100.0 + (index % 2),
            )
        )

    for index in range(5):
        db.add(
            MetricEvent(
                service_id=service.id,
                timestamp=base_time
                - timedelta(minutes=5 - index),
                name="checkout_latency",
                value=160.0 + index,
            )
        )

    db.flush()

    current_metric = MetricEvent(
        service_id=service.id,
        timestamp=base_time,
        name="checkout_latency",
        value=180.0,
    )
    db.add(current_metric)

    db.add(
        LogEvent(
            service_id=service.id,
            timestamp=base_time + timedelta(seconds=30),
            level="ERROR",
            message="Payment provider timeout",
        )
    )

    db.add(
        DeploymentEvent(
            service_id=service.id,
            timestamp=base_time - timedelta(seconds=60),
            version="checkout-v42",
            description="Checkout deployment",
        )
    )

    db.commit()

    incident = process_metric_event_for_incident(
        db=db,
        metric_event_id=current_metric.id,
    )

    assert incident is not None

    return incident


def test_persist_investigation_result_with_evidence():
    db = SessionLocal()

    try:
        incident = create_test_incident(db)

        investigation = Investigation(
            incident_id=incident.id,
            status="pending",
        )
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        evidence_items = (
            db.query(EvidenceItem)
            .filter(
                EvidenceItem.incident_id == incident.id,
            )
            .all()
        )

        assert len(evidence_items) >= 3

        supporting_ids = [
            evidence_items[0].id,
            evidence_items[1].id,
        ]

        result_context = InvestigationResultContext(
            hypothesis=InvestigationHypothesis(
                hypothesis=(
                    "The checkout deployment may have contributed "
                    "to the latency increase."
                ),
                confidence=0.82,
                reasoning=(
                    "The latency anomaly occurred near the deployment "
                    "and was accompanied by an error signal."
                ),
                supporting_evidence_ids=supporting_ids,
                alternative_explanations=[
                    "External payment-provider degradation.",
                ],
                next_steps=[
                    "Compare latency before and after deployment.",
                    "Inspect payment-provider latency.",
                ],
            )
        )

        result = persist_investigation_result(
            db=db,
            investigation=investigation,
            result_context=result_context,
        )

        assert result.id is not None
        assert result.investigation_id == investigation.id
        assert result.hypothesis == (
            "The checkout deployment may have contributed "
            "to the latency increase."
        )
        assert result.confidence == 0.82
        assert "Compare latency" in result.next_steps

        links = (
            db.query(InvestigationResultEvidence)
            .filter(
                InvestigationResultEvidence.investigation_result_id
                == result.id
            )
            .all()
        )

        assert len(links) == 2

        linked_ids = {
            link.evidence_item_id
            for link in links
        }

        assert linked_ids == set(supporting_ids)

    finally:
        db.rollback()
        db.close()


def test_persist_investigation_result_rejects_cross_incident_evidence():
    db = SessionLocal()

    try:
        incident_a = create_test_incident(db)

        investigation = Investigation(
            incident_id=incident_a.id,
            status="pending",
        )
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        # Create an unrelated incident and evidence item.
        user = db.query(User).filter(
            User.email.like("result-%@example.com")
        ).first()

        assert user is not None

        project = db.query(Project).filter(
            Project.owner_id == user.id
        ).first()

        assert project is not None

        incident_b = Incident(
            project_id=project.id,
            title="Unrelated incident",
            description="Evidence must not cross incident boundaries.",
            severity="medium",
            status="open",
            detected_at=datetime.now(timezone.utc),
        )
        db.add(incident_b)
        db.flush()

        unrelated_evidence = EvidenceItem(
            incident_id=incident_b.id,
            source_type="telemetry",
            source_id=uuid4(),
            title="Unrelated evidence",
            description="This belongs to another incident.",
            collected_at=datetime.now(timezone.utc),
        )
        db.add(unrelated_evidence)
        db.commit()
        db.refresh(unrelated_evidence)

        result_context = InvestigationResultContext(
            hypothesis=InvestigationHypothesis(
                hypothesis="Potential unrelated cause.",
                confidence=0.50,
                reasoning="This evidence belongs to another incident.",
                supporting_evidence_ids=[
                    unrelated_evidence.id,
                ],
                alternative_explanations=[],
                next_steps=[
                    "Investigate the evidence separately.",
                ],
            )
        )

        with pytest.raises(
            ValueError,
            match="do not belong to the investigation incident",
        ):
            persist_investigation_result(
                db=db,
                investigation=investigation,
                result_context=result_context,
            )

        persisted_results = (
            db.query(InvestigationResult)
            .filter(
                InvestigationResult.investigation_id
                == investigation.id
            )
            .all()
        )

        assert persisted_results == []

    finally:
        db.rollback()
        db.close()