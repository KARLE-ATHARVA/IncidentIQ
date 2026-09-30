from uuid import uuid4

import pytest

from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
    InvestigationHypothesis,
    InvestigationResultContext,
)
from backend.app.services.investigation_reasoning import (
    DeterministicReasoner,
    generate_deterministic_investigation,
)
from backend.app.services.reasoning_engine import ReasoningEngine


class StubReasoningEngine(ReasoningEngine):
    def generate(
        self,
        context: InvestigationContext,
    ) -> InvestigationResultContext:
        evidence_id = uuid4()

        hypothesis = InvestigationHypothesis(
            hypothesis="The incident may be related to the observed service degradation.",
            confidence=0.5,
            reasoning="This is a controlled test implementation.",
            supporting_evidence_ids=[evidence_id],
            alternative_explanations=[
                "The degradation may have another underlying cause."
            ],
            next_steps=[
                "Inspect the available telemetry for additional evidence."
            ],
        )

        return InvestigationResultContext(
            investigation_id=uuid4(),
            incident_id=context.incident.incident_id,
            hypothesis=hypothesis,
        )


def build_context(
    *,
    timeline_events: list[dict] | None = None,
    evidence_count: int = 1,
) -> InvestigationContext:
    incident_id = uuid4()

    incident = IncidentContext(
        incident_id=incident_id,
        title="Test incident",
        description="Controlled test incident.",
        severity="high",
        status="investigating",
        detected_at=None,
        resolved_at=None,
    )

    evidence_items = [
        EvidenceContext(
            evidence_id=uuid4(),
            source_type="metric",
            source_id=uuid4(),
            title=f"Evidence {index + 1}",
            description="Controlled test evidence.",
            collected_at=None,
        )
        for index in range(evidence_count)
    ]

    return InvestigationContext(
        incident=incident,
        timeline_events=timeline_events or [],
        evidence_items=evidence_items,
        historical_incidents=[],
    )


def test_reasoning_engine_can_be_implemented():
    engine = StubReasoningEngine()
    context = build_context()

    result = engine.generate(context)

    assert isinstance(result, InvestigationResultContext)
    assert result.incident_id == context.incident.incident_id
    assert result.hypothesis.hypothesis
    assert 0.0 <= result.hypothesis.confidence <= 1.0


def test_reasoning_engine_is_an_abstract_contract():
    assert ReasoningEngine.__abstractmethods__ == {"generate"}


def test_deterministic_reasoner_uses_deployment_error_and_metric_signals():
    context = build_context(
        timeline_events=[
            {
                "event_type": "deployment",
                "timestamp": "2026-09-24T10:00:00Z",
            },
            {
                "event_type": "log",
                "timestamp": "2026-09-24T10:01:00Z",
                "severity": "error",
            },
            {
                "event_type": "metric",
                "timestamp": "2026-09-24T10:02:00Z",
            },
        ]
    )

    result = DeterministicReasoner().generate(context)

    assert result.hypothesis.confidence == 0.70
    assert "deployment may have contributed" in result.hypothesis.hypothesis
    assert len(result.hypothesis.alternative_explanations) == 2
    assert len(result.hypothesis.next_steps) == 3
    assert result.hypothesis.supporting_evidence_ids == [
        evidence.evidence_id for evidence in context.evidence_items
    ]


def test_deterministic_reasoner_uses_error_and_metric_signals():
    context = build_context(
        timeline_events=[
            {
                "event_type": "log",
                "timestamp": "2026-09-24T10:01:00Z",
                "severity": "critical",
            },
            {
                "event_type": "metric",
                "timestamp": "2026-09-24T10:02:00Z",
            },
        ]
    )

    result = DeterministicReasoner().generate(context)

    assert result.hypothesis.confidence == 0.60
    assert "metric anomaly may be associated" in result.hypothesis.hypothesis
    assert len(result.hypothesis.alternative_explanations) == 2
    assert len(result.hypothesis.next_steps) == 3


def test_deterministic_reasoner_uses_fallback_when_signals_are_insufficient():
    context = build_context(
        timeline_events=[
            {
                "event_type": "metric",
                "timestamp": "2026-09-24T10:02:00Z",
            }
        ]
    )

    result = DeterministicReasoner().generate(context)

    assert result.hypothesis.confidence == 0.35
    assert "insufficient" in result.hypothesis.hypothesis
    assert "Insufficient telemetry." in result.hypothesis.alternative_explanations
    assert len(result.hypothesis.next_steps) == 3


def test_deterministic_reasoner_requires_evidence():
    context = build_context(
        timeline_events=[
            {
                "event_type": "metric",
                "timestamp": "2026-09-24T10:02:00Z",
            }
        ],
        evidence_count=0,
    )

    with pytest.raises(
        ValueError,
        match="Cannot generate an investigation result without evidence",
    ):
        DeterministicReasoner().generate(context)


def test_backward_compatible_deterministic_helper():
    context = build_context(
        timeline_events=[
            {
                "event_type": "log",
                "timestamp": "2026-09-24T10:01:00Z",
                "severity": "error",
            },
            {
                "event_type": "metric",
                "timestamp": "2026-09-24T10:02:00Z",
            },
        ]
    )

    result = generate_deterministic_investigation(context)

    assert isinstance(result, InvestigationResultContext)
    assert result.hypothesis.confidence == 0.60
    assert result.hypothesis.hypothesis