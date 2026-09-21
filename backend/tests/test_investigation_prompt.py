from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.investigation_context import (
    EvidenceContext,
    HistoricalIncidentContext,
    IncidentContext,
    InvestigationContext,
)
from backend.app.services.investigation_prompt import (
    SYSTEM_INSTRUCTION,
    build_reasoning_input,
)


def create_context() -> InvestigationContext:
    incident_id = uuid4()
    evidence_id = uuid4()
    service_id = uuid4()

    return InvestigationContext(
        incident=IncidentContext(
            incident_id=incident_id,
            title="Checkout latency incident",
            description="Checkout latency increased unexpectedly.",
            severity="high",
            status="open",
            detected_at=datetime.now(timezone.utc),
            resolved_at=None,
        ),
        timeline_events=[
            {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "metric",
                "service_id": str(service_id),
                "title": "Checkout latency anomaly",
                "description": "Latency exceeded the historical baseline.",
                "source_id": str(uuid4()),
                "severity": None,
                "metadata": {"value": 175},
            }
        ],
        evidence_items=[
            EvidenceContext(
                evidence_id=evidence_id,
                source_type="telemetry",
                source_id=uuid4(),
                title="Supporting telemetry evidence",
                description="Latency anomaly supporting the incident.",
                collected_at=datetime.now(timezone.utc),
            )
        ],
        historical_incidents=[
            HistoricalIncidentContext(
                historical_incident_id=uuid4(),
                title="Previous checkout latency incident",
                summary="Checkout latency increased after an operational change.",
                symptoms="Elevated checkout latency.",
                root_cause="Database contention",
                resolution="Database capacity was increased.",
                severity="high",
                service_id=service_id,
                occurred_at=datetime.now(timezone.utc),
                similarity_score=0.76,
            )
        ],
    )


def test_build_reasoning_input_contains_controlled_context():
    context = create_context()

    reasoning_input = build_reasoning_input(context)

    assert reasoning_input.system_instruction == SYSTEM_INSTRUCTION.strip()
    assert "incident" in reasoning_input.investigation_context
    assert "timeline_events" in reasoning_input.investigation_context
    assert "evidence_items" in reasoning_input.investigation_context
    assert "historical_incidents" in reasoning_input.investigation_context


def test_system_instruction_contains_safety_rules():
    assert "ONLY the investigation context" in SYSTEM_INSTRUCTION
    assert "Never invent" in SYSTEM_INSTRUCTION
    assert "hypothesis is not a confirmed root cause" in SYSTEM_INSTRUCTION
    assert "historical incident" in SYSTEM_INSTRUCTION
