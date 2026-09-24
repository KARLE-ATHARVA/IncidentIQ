from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.investigation_context import (
    EvidenceContext,
    HistoricalIncidentContext,
    IncidentContext,
    InvestigationContext,
    serialize_investigation_context,
)


def test_rag_context_serialization_preserves_evidence_provenance():
    incident_id = uuid4()
    evidence_id = uuid4()
    source_id = uuid4()
    historical_id = uuid4()
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
        historical_incidents=[
            HistoricalIncidentContext(
                historical_incident_id=historical_id,
                title="Previous checkout latency incident",
                summary="Checkout latency increased after a deployment.",
                symptoms="Elevated latency and timeout errors.",
                root_cause="Connection pool exhaustion.",
                resolution="Increased connection pool capacity.",
                severity="high",
                service_id=service_id,
                occurred_at=detected_at,
                similarity_score=0.91,
            )
        ],
    )

    serialized = serialize_investigation_context(context)

    assert serialized["incident"]["incident_id"] == str(incident_id)

    assert len(serialized["timeline_events"]) == 1
    assert serialized["timeline_events"][0]["source_id"] == str(source_id)

    assert len(serialized["evidence_items"]) == 1
    assert serialized["evidence_items"][0]["evidence_id"] == str(evidence_id)
    assert serialized["evidence_items"][0]["source_id"] == str(source_id)

    assert len(serialized["historical_incidents"]) == 1
    assert (
        serialized["historical_incidents"][0]["historical_incident_id"]
        == str(historical_id)
    )
    assert (
        serialized["historical_incidents"][0]["similarity_score"]
        == 0.91
    )