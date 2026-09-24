from uuid import uuid4

import pytest

from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
    InvestigationHypothesis,
    validate_supporting_evidence_against_context,
)


def build_context() -> InvestigationContext:
    incident_id = uuid4()
    evidence_id = uuid4()

    incident = IncidentContext(
        incident_id=incident_id,
        title="Checkout incident",
        description="Checkout latency increased.",
        severity="high",
        status="investigating",
        detected_at=None,
        resolved_at=None,
    )

    evidence = EvidenceContext(
        evidence_id=evidence_id,
        source_type="metric",
        source_id=uuid4(),
        title="Checkout latency",
        description="Latency increased during the incident window.",
        collected_at=None,
    )

    return InvestigationContext(
        incident=incident,
        timeline_events=[],
        evidence_items=[evidence],
        historical_incidents=[],
    )


def test_valid_ai_evidence_reference_is_accepted():
    context = build_context()

    hypothesis = InvestigationHypothesis(
        hypothesis="The latency increase may be related to service degradation.",
        confidence=0.7,
        reasoning="The metric evidence shows increased latency.",
        supporting_evidence_ids=[
            context.evidence_items[0].evidence_id
        ],
        alternative_explanations=[
            "An external dependency may have contributed."
        ],
        next_steps=[
            "Inspect service behavior during the incident window."
        ],
    )

    validate_supporting_evidence_against_context(
        context,
        hypothesis,
    )


def test_unknown_ai_evidence_reference_is_rejected():
    context = build_context()

    unknown_evidence_id = uuid4()

    hypothesis = InvestigationHypothesis(
        hypothesis="The incident may be related to a deployment.",
        confidence=0.7,
        reasoning="The model claims a deployment was involved.",
        supporting_evidence_ids=[unknown_evidence_id],
        alternative_explanations=[
            "The issue may have originated from infrastructure."
        ],
        next_steps=[
            "Inspect deployment activity around the incident."
        ],
    )

    with pytest.raises(
        ValueError,
        match="supporting evidence items are not present",
    ):
        validate_supporting_evidence_against_context(
            context,
            hypothesis,
        )