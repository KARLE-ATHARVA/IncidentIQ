import time
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
)
from backend.app.services.investigation_reasoning import (
    DeterministicReasoner,
)


def create_context():
    incident = IncidentContext(
        incident_id=uuid4(),
        title="Checkout latency incident",
        description="Checkout latency increased.",
        severity="high",
        status="investigating",
        detected_at=datetime.now(timezone.utc),
        resolved_at=None,
    )

    evidence_items = [
        EvidenceContext(
            evidence_id=uuid4(),
            source_type="metric",
            source_id=uuid4(),
            title="Checkout latency anomaly",
            description="Checkout latency increased significantly.",
            collected_at=datetime.now(timezone.utc),
        ),
        EvidenceContext(
            evidence_id=uuid4(),
            source_type="log",
            source_id=uuid4(),
            title="Checkout error",
            description="Checkout requests returned errors.",
            collected_at=datetime.now(timezone.utc),
        ),
        EvidenceContext(
            evidence_id=uuid4(),
            source_type="deployment",
            source_id=uuid4(),
            title="Checkout deployment",
            description="Version v2.4.0 was deployed.",
            collected_at=datetime.now(timezone.utc),
        ),
    ]

    timeline_events = [
        {
            "event_type": "metric",
            "timestamp": datetime.now(timezone.utc),
            "severity": None,
        },
        {
            "event_type": "log",
            "timestamp": datetime.now(timezone.utc),
            "severity": "ERROR",
        },
        {
            "event_type": "deployment",
            "timestamp": datetime.now(timezone.utc),
            "severity": None,
        },
    ]

    return InvestigationContext(
        incident=incident,
        timeline_events=timeline_events,
        evidence_items=evidence_items,
        historical_incidents=[],
    )


def test_deterministic_reasoning_performance():
    context = create_context()
    reasoner = DeterministicReasoner()

    iteration_count = 10_000

    start_time = time.perf_counter()

    for _ in range(iteration_count):
        result = reasoner.generate(context)

    elapsed_seconds = time.perf_counter() - start_time

    average_latency_us = (
        elapsed_seconds / iteration_count
    ) * 1_000_000

    throughput = iteration_count / elapsed_seconds

    print("\n" + "=" * 60)
    print("INCIDENTIQ DETERMINISTIC REASONING PERFORMANCE")
    print("=" * 60)
    print(f"Iterations:             {iteration_count}")
    print(f"Total time:             {elapsed_seconds:.4f} s")
    print(
        f"Average latency:        "
        f"{average_latency_us:.2f} µs"
    )
    print(
        f"Throughput:             "
        f"{throughput:.2f} reasoning/s"
    )
    print(
        f"Confidence:             "
        f"{result.hypothesis.confidence:.2f}"
    )
    print("=" * 60)

    assert result.hypothesis.confidence == 0.70
    assert elapsed_seconds > 0
    assert average_latency_us > 0
    assert throughput > 0
