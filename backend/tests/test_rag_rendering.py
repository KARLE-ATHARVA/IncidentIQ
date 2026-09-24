import json
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
    build_reasoning_input,
    render_reasoning_input_as_text,
)


def test_reasoning_input_renders_as_deterministic_json():
    incident_id = uuid4()
    evidence_id = uuid4()
    source_id = uuid4()
    service_id = uuid4()

    detected_at = datetime.now(timezone.utc)

    context = InvestigationContext(
        incident=IncidentContext(
            incident_id=incident_id,
            title="Checkout latency incident",
            description="Checkout latency increased significantly.",
            severity="high",
            status="investigating",
            detected_at=detected_at,
            resolved_at=None,
        ),
        timeline_events=[
            {
                "id": str(uuid4()),
                "timestamp": detected_at.isoformat(),
                "event_type": "metric",
                "service_id": str(service_id),
                "title": "Checkout latency anomaly",
                "description": "Latency exceeded the baseline.",
                "source_id": str(source_id),
                "severity": "high",
                "metadata": {
                    "metric_name": "checkout_latency",
                    "value": 175.0,
                },
            }
        ],
        evidence_items=[
            EvidenceContext(
                evidence_id=evidence_id,
                source_type="metric",
                source_id=source_id,
                title="Checkout latency anomaly",
                description="Latency exceeded the normal baseline.",
                collected_at=detected_at,
            )
        ],
        historical_incidents=[],
    )

    reasoning_input = build_reasoning_input(context)

    rendered = render_reasoning_input_as_text(reasoning_input)

    parsed = json.loads(rendered)

    assert parsed["system_instruction"] == reasoning_input.system_instruction

    assert (
        parsed["investigation_context"]["incident"]["incident_id"]
        == str(incident_id)
    )

    assert (
        parsed["investigation_context"]["evidence_items"][0]["evidence_id"]
        == str(evidence_id)
    )

    # Rendering should be deterministic for the same input.
    assert rendered == render_reasoning_input_as_text(reasoning_input)