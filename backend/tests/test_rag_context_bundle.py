from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.models.incident import Incident
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.investigation_context import (
    build_investigation_context,
)


def test_rag_context_bundle_contains_operational_and_historical_evidence(
    db_session,
):
    user = User(
        id=uuid4(),
        email=f"rag-test-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    project = Project(
        id=uuid4(),
        name="RAG Test Project",
        owner_id=user.id,
    )
    service = Service(
        id=uuid4(),
        project_id=project.id,
        name="checkout-service",
    )

    db_session.add(user)
    db_session.add(project)
    db_session.add(service)
    db_session.flush()

    detected_at = datetime.now(timezone.utc)

    incident = Incident(
        id=uuid4(),
        project_id=project.id,
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status="investigating",
        detected_at=detected_at,
    )

    db_session.add(incident)
    db_session.flush()

    metric = MetricEvent(
        id=uuid4(),
        service_id=service.id,
        timestamp=detected_at,
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
        description="Checkout latency increased above the normal baseline.",
        collected_at=detected_at,
    )

    db_session.add(evidence)

    historical_incident = HistoricalIncident(
        id=uuid4(),
        incident_id=incident.id,
        project_id=project.id,
        service_id=service.id,
        title="Previous checkout latency incident",
        summary="Checkout latency increased after a deployment.",
        symptoms="Elevated checkout latency and timeout errors.",
        root_cause="Connection pool exhaustion.",
        resolution="Increased connection pool capacity.",
        severity="high",
        occurred_at=detected_at - timedelta(days=30),
        resolved_at=detected_at - timedelta(days=30, hours=-1),
    )

    db_session.add(historical_incident)
    db_session.flush()

    embedding = HistoricalIncidentEmbedding(
        id=uuid4(),
        historical_incident_id=historical_incident.id,
        embedding=[1.0] + [0.0] * 383,
        model_name="test-model",
        embedding_text="Previous checkout latency incident",
    )

    db_session.add(embedding)
    db_session.commit()

    context = build_investigation_context(
        db=db_session,
        incident=incident,
        top_k=5,
        similarity_threshold=0.0,
    )

    assert context.incident.incident_id == incident.id
    assert context.incident.title == "Checkout latency incident"

    assert len(context.timeline_events) >= 1

    assert len(context.evidence_items) == 1
    assert context.evidence_items[0].evidence_id == evidence.id
    assert (
        context.evidence_items[0].description
        == "Checkout latency increased above the normal baseline."
    )

    assert len(context.historical_incidents) == 1
    assert (
        context.historical_incidents[0].historical_incident_id
        == historical_incident.id
    )
    assert (
        context.historical_incidents[0].root_cause
        == "Connection pool exhaustion."
    )
    assert (
        context.historical_incidents[0].resolution
        == "Increased connection pool capacity."
    )