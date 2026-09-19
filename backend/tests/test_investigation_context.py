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
from backend.app.services.historical_retrieval import (
    RetrievedHistoricalIncident,
)
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)
from backend.app.services.investigation_context import (
    InvestigationContext,
    InvestigationHypothesis,
    InvestigationResultContext,
    IncidentContext,
    ReasoningInput,
    build_investigation_context,
    build_reasoning_input,
    render_reasoning_input_as_text,
    serialize_investigation_context,
    serialize_investigation_result,
    validate_investigation_hypothesis,
)


def test_build_investigation_context_from_real_incident():
    db = SessionLocal()

    try:
        user = User(
            email=f"context-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db.add(user)
        db.flush()

        project = Project(
            name="Investigation Context Test Project",
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
                - timedelta(minutes=25 - index),
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
        # Run the real incident pipeline
        # -----------------------------------------------------

        incident = process_metric_event_for_incident(
            db=db,
            metric_event_id=current_metric.id,
        )

        assert incident is not None

        # -----------------------------------------------------
        # Verify the pipeline produced evidence
        # -----------------------------------------------------

        evidence_items = (
            db.query(EvidenceItem)
            .filter(
                EvidenceItem.incident_id == incident.id,
            )
            .all()
        )

        assert len(evidence_items) >= 3

        # -----------------------------------------------------
        # Fake only the historical retrieval boundary
        # -----------------------------------------------------

        historical_result = RetrievedHistoricalIncident(
            historical_incident_id=uuid4(),
            title="Previous checkout latency incident",
            summary="Checkout latency increased after a deployment.",
            symptoms="Elevated checkout latency and payment timeouts.",
            root_cause=(
                "Deployment introduced a slow payment-provider call."
            ),
            resolution="Rolled back the deployment.",
            severity="high",
            service_id=service.id,
            occurred_at=base_time - timedelta(days=7),
            similarity_score=0.82,
        )

        import backend.app.services.investigation_context as context_module

        original_retrieval = (
            context_module.retrieve_historical_context
        )

        context_module.retrieve_historical_context = (
            lambda **kwargs: [historical_result]
        )

        try:
            # -------------------------------------------------
            # Build the investigation context
            # -------------------------------------------------

            context = build_investigation_context(
                db=db,
                incident=incident,
            )
        finally:
            context_module.retrieve_historical_context = (
                original_retrieval
            )

        # -----------------------------------------------------
        # Verify incident context
        # -----------------------------------------------------

        assert context.incident.incident_id == incident.id
        assert context.incident.title == incident.title
        assert context.incident.severity == incident.severity
        assert context.incident.status == "open"
        assert context.incident.detected_at == incident.detected_at

        # -----------------------------------------------------
        # Verify timeline
        # -----------------------------------------------------

        assert len(context.timeline_events) > 0

        timeline_types = {
            event["event_type"]
            for event in context.timeline_events
        }

        assert "metric" in timeline_types
        assert "log" in timeline_types
        assert "deployment" in timeline_types

        timeline_timestamps = [
            datetime.fromisoformat(
                event["timestamp"].replace("Z", "+00:00")
            )
            for event in context.timeline_events
        ]

        assert timeline_timestamps == sorted(timeline_timestamps)

        # -----------------------------------------------------
        # Verify evidence
        # -----------------------------------------------------

        assert len(context.evidence_items) >= 3

        evidence_source_ids = {
            evidence.source_id
            for evidence in context.evidence_items
        }

        assert current_metric.id in evidence_source_ids
        assert error_log.id in evidence_source_ids
        assert deployment.id in evidence_source_ids

        # -----------------------------------------------------
        # Verify historical context
        # -----------------------------------------------------

        assert len(context.historical_incidents) == 1

        historical = context.historical_incidents[0]

        assert (
            historical.historical_incident_id
            == historical_result.historical_incident_id
        )
        assert historical.title == historical_result.title
        assert historical.similarity_score == 0.82
        assert historical.root_cause is not None
        assert historical.resolution is not None

    finally:
        db.rollback()
        db.close()


def test_serialize_investigation_context():
    db = SessionLocal()

    try:
        user = User(
            email=f"serialization-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db.add(user)
        db.flush()

        project = Project(
            name="Serialization Test Project",
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
            db.add(
                MetricEvent(
                    service_id=service.id,
                    timestamp=base_time
                    - timedelta(minutes=25 - index),
                    name="checkout_latency",
                    value=100.0 + (index % 2),
                )
            )

        # -----------------------------------------------------
        # Recent anomalous observations
        # -----------------------------------------------------

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

        db.add(
            LogEvent(
                service_id=service.id,
                timestamp=base_time + timedelta(seconds=30),
                level="ERROR",
                message="Payment provider timeout",
            )
        )

        # -----------------------------------------------------
        # Correlated deployment
        # -----------------------------------------------------

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

        historical_result = RetrievedHistoricalIncident(
            historical_incident_id=uuid4(),
            title="Previous checkout latency incident",
            summary="Checkout latency increased after deployment.",
            symptoms="Elevated latency and payment timeouts.",
            root_cause="Slow payment-provider call.",
            resolution="Rolled back the deployment.",
            severity="high",
            service_id=service.id,
            occurred_at=base_time - timedelta(days=7),
            similarity_score=0.82,
        )

        import backend.app.services.investigation_context as context_module

        original_retrieval = (
            context_module.retrieve_historical_context
        )

        context_module.retrieve_historical_context = (
            lambda **kwargs: [historical_result]
        )

        try:
            context = build_investigation_context(
                db=db,
                incident=incident,
            )
        finally:
            context_module.retrieve_historical_context = (
                original_retrieval
            )

        serialized = serialize_investigation_context(context)

        assert isinstance(serialized, dict)

        assert set(serialized.keys()) == {
            "incident",
            "timeline_events",
            "evidence_items",
            "historical_incidents",
        }

        assert (
            serialized["incident"]["incident_id"]
            == str(incident.id)
        )

        assert isinstance(
            serialized["incident"]["detected_at"],
            str,
        )

        assert len(serialized["timeline_events"]) > 0
        assert len(serialized["evidence_items"]) >= 3
        assert len(serialized["historical_incidents"]) == 1

        historical = serialized["historical_incidents"][0]

        assert (
            historical["historical_incident_id"]
            == str(historical_result.historical_incident_id)
        )

        assert historical["similarity_score"] == 0.82

    finally:
        db.rollback()
        db.close()


def test_investigation_result_serialization():
    evidence_id = uuid4()

    hypothesis = InvestigationHypothesis(
        hypothesis=(
            "The checkout deployment may have contributed to "
            "the observed latency increase."
        ),
        confidence=0.82,
        reasoning=(
            "The latency anomaly occurred shortly after the deployment "
            "and was accompanied by payment-provider timeout errors."
        ),
        supporting_evidence_ids=[
            evidence_id,
        ],
        alternative_explanations=[
            "External payment-provider degradation.",
            "Database contention.",
        ],
        next_steps=[
            "Compare checkout latency before and after the deployment.",
            "Inspect payment-provider response latency.",
            "Review database connection utilization.",
        ],
    )

    result = InvestigationResultContext(
        hypothesis=hypothesis,
    )

    serialized = serialize_investigation_result(result)

    assert serialized["hypothesis"] == hypothesis.hypothesis
    assert serialized["confidence"] == 0.82
    assert serialized["reasoning"] == hypothesis.reasoning
    assert serialized["supporting_evidence_ids"] == [
        str(evidence_id)
    ]
    assert len(serialized["alternative_explanations"]) == 2
    assert len(serialized["next_steps"]) == 3


def test_investigation_hypothesis_rejects_invalid_confidence():
    hypothesis = InvestigationHypothesis(
        hypothesis="Possible deployment-related issue.",
        confidence=1.5,
        reasoning="Deployment occurred shortly before the anomaly.",
        supporting_evidence_ids=[uuid4()],
        alternative_explanations=[],
        next_steps=["Inspect deployment changes."],
    )

    try:
        validate_investigation_hypothesis(hypothesis)
        assert False, "Expected invalid confidence to raise ValueError."
    except ValueError as exc:
        assert "confidence" in str(exc).lower()


def test_investigation_hypothesis_requires_supporting_evidence():
    hypothesis = InvestigationHypothesis(
        hypothesis="Possible deployment-related issue.",
        confidence=0.70,
        reasoning="Deployment occurred shortly before the anomaly.",
        supporting_evidence_ids=[],
        alternative_explanations=[],
        next_steps=["Inspect deployment changes."],
    )

    try:
        validate_investigation_hypothesis(hypothesis)
        assert False, "Expected missing evidence to raise ValueError."
    except ValueError as exc:
        assert "evidence" in str(exc).lower()


def test_build_reasoning_input():
    incident = IncidentContext(
        incident_id=uuid4(),
        title="Checkout latency incident",
        description="Checkout latency exceeded the expected baseline.",
        severity="high",
        status="open",
        detected_at=datetime.now(timezone.utc),
        resolved_at=None,
    )

    context = InvestigationContext(
        incident=incident,
        timeline_events=[
            {
                "id": str(uuid4()),
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "event_type": "metric",
                "service_id": str(uuid4()),
                "title": "checkout_latency",
                "description": "checkout_latency = 180.0",
                "source_id": str(uuid4()),
                "severity": None,
                "metadata": {
                    "metric_name": "checkout_latency",
                    "value": 180.0,
                },
            }
        ],
        evidence_items=[],
        historical_incidents=[],
    )

    reasoning_input = build_reasoning_input(context)

    assert isinstance(reasoning_input, ReasoningInput)

    assert (
        reasoning_input.investigation_context["incident"]["title"]
        == "Checkout latency incident"
    )

    assert "Do not invent telemetry" in (
        reasoning_input.system_instruction
    )

    rendered = render_reasoning_input_as_text(
        reasoning_input
    )

    assert isinstance(rendered, str)
    assert "Checkout latency incident" in rendered
    assert "checkout_latency" in rendered


def test_reasoning_input_contains_no_database_objects():
    incident = IncidentContext(
        incident_id=uuid4(),
        title="Test incident",
        description=None,
        severity="medium",
        status="open",
        detected_at=datetime.now(timezone.utc),
        resolved_at=None,
    )

    context = InvestigationContext(
        incident=incident,
        timeline_events=[],
        evidence_items=[],
        historical_incidents=[],
    )

    reasoning_input = build_reasoning_input(context)

    serialized = reasoning_input.investigation_context

    assert isinstance(serialized, dict)
    assert isinstance(
        serialized["incident"]["incident_id"],
        str,
    )
    assert isinstance(
        serialized["incident"]["detected_at"],
        str,
    )