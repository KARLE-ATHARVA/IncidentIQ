from types import SimpleNamespace
from uuid import uuid4

from backend.app.services.investigation_context import (
    InvestigationHypothesis,
)
from backend.app.services.investigation_evaluation import (
    evaluate_investigation_result,
)


def make_evidence():
    return SimpleNamespace(
        evidence_id=uuid4(),
        source_type="telemetry",
        source_id=uuid4(),
        title="Checkout latency anomaly",
        description="Checkout latency increased after a deployment.",
    )


def make_context(evidence):
    return SimpleNamespace(
        evidence_items=[evidence],
        timeline_events=[SimpleNamespace()],
        historical_incidents=[SimpleNamespace()],
    )


def make_valid_hypothesis(evidence):
    return InvestigationHypothesis(
        hypothesis=(
            "The recent deployment may have contributed to "
            "the checkout latency incident."
        ),
        confidence=0.70,
        reasoning=(
            "The deployment occurred near the observed latency "
            "increase and is supported by telemetry evidence."
        ),
        supporting_evidence_ids=[evidence.evidence_id],
        alternative_explanations=[
            "External dependency degradation.",
            "Database contention.",
        ],
        next_steps=[
            "Compare telemetry before and after the deployment.",
            "Inspect external dependency health.",
        ],
    )


def test_deterministic_fallback_result_is_validated():
    evidence = make_evidence()
    context = make_context(evidence)
    hypothesis = make_valid_hypothesis(evidence)

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="deterministic_fallback",
    )

    assert evaluation.is_valid is True
    assert evaluation.errors == []
    assert evaluation.evidence_count == 1
    assert evaluation.supporting_evidence_count == 1
    assert evaluation.evidence_coverage == 1.0


def test_invalid_fallback_result_is_rejected():
    evidence = make_evidence()
    context = make_context(evidence)

    invalid_hypothesis = InvestigationHypothesis(
        hypothesis="Some unsupported hypothesis.",
        confidence=0.70,
        reasoning="This reasoning references unavailable evidence.",
        supporting_evidence_ids=[uuid4()],
        alternative_explanations=[
            "Another possible explanation.",
        ],
        next_steps=[
            "Investigate further.",
        ],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=invalid_hypothesis,
        reasoning_source="deterministic_fallback",
    )

    assert evaluation.is_valid is False
    assert any(
        "not present in the investigation context" in error
        for error in evaluation.errors
    )