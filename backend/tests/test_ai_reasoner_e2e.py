from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.services.ai_reasoner import AIReasoner
from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
)


def create_real_ai_context() -> InvestigationContext:
    """
    Create a small but realistic investigation context for the
    real Ollama/Qwen integration test.
    """

    service_id = uuid4()

    evidence_id = uuid4()

    return InvestigationContext(
        incident=IncidentContext(
            incident_id=uuid4(),
            title="Checkout latency incident",
            description=(
                "Checkout latency increased significantly during "
                "the incident window."
            ),
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
                "description": (
                    "Checkout latency increased from the normal "
                    "baseline to approximately 180 ms."
                ),
                "source_id": str(uuid4()),
                "severity": None,
                "metadata": {
                    "metric_name": "checkout_latency",
                    "value": 180.0,
                    "baseline": 100.5,
                },
            },
            {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "log",
                "service_id": str(service_id),
                "title": "Payment provider timeout",
                "description": (
                    "Payment provider requests experienced timeout errors."
                ),
                "source_id": str(uuid4()),
                "severity": "ERROR",
                "metadata": {
                    "level": "ERROR",
                },
            },
            {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "deployment",
                "service_id": str(service_id),
                "title": "Checkout deployment",
                "description": (
                    "Checkout service version checkout-v42 was deployed."
                ),
                "source_id": str(uuid4()),
                "severity": None,
                "metadata": {
                    "version": "checkout-v42",
                },
            },
        ],
        evidence_items=[
            EvidenceContext(
                evidence_id=evidence_id,
                source_type="telemetry",
                source_id=uuid4(),
                title="Checkout latency telemetry",
                description=(
                    "Checkout latency increased to approximately "
                    "180 ms compared with a baseline of approximately "
                    "100 ms."
                ),
                collected_at=datetime.now(timezone.utc),
            ),
        ],
        historical_incidents=[],
    )


@pytest.mark.integration
def test_ai_reasoner_real_ollama_generation():
    """
    Real integration test.

    This intentionally calls:
        AIReasoner -> Ollama -> Qwen2.5 3B

    It is NOT part of the normal test suite.
    """

    context = create_real_ai_context()

    reasoner = AIReasoner()

    try:
        result = reasoner.generate(context)

    except RuntimeError as exc:
        pytest.fail(
            f"Real Ollama integration test could not connect to Ollama: {exc}"
        )

    assert result is not None

    hypothesis = result.hypothesis

    assert hypothesis.hypothesis
    assert 0.0 <= hypothesis.confidence <= 1.0

    assert hypothesis.reasoning

    assert hypothesis.supporting_evidence_ids

    assert len(hypothesis.alternative_explanations) >= 1

    assert len(hypothesis.next_steps) >= 1

    available_evidence_ids = {
        evidence.evidence_id
        for evidence in context.evidence_items
    }

    assert set(hypothesis.supporting_evidence_ids).issubset(
        available_evidence_ids
    )