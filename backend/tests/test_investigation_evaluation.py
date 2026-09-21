from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.services.investigation_context import (
    InvestigationHypothesis,
)
from backend.app.services.investigation_evaluation import (
    evaluate_investigation_result,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def make_evidence():
    return SimpleNamespace(
        evidence_id=uuid4(),
        source_type="telemetry",
        source_id=uuid4(),
        title="Checkout latency anomaly",
        description="Checkout latency increased significantly.",
    )


def make_context(
    evidence_items=None,
    timeline_events=None,
    historical_incidents=None,
):
    return SimpleNamespace(
        evidence_items=evidence_items or [],
        timeline_events=(
            timeline_events
            if timeline_events is not None
            else [SimpleNamespace()]
        ),
        historical_incidents=(
            historical_incidents
            if historical_incidents is not None
            else [SimpleNamespace()]
        ),
    )


def make_hypothesis(
    supporting_evidence_ids,
    confidence=0.7,
):
    return InvestigationHypothesis(
        hypothesis="A recent deployment may have contributed to the incident.",
        confidence=confidence,
        reasoning=(
            "The deployment occurred near the observed latency increase "
            "and is supported by the available telemetry evidence."
        ),
        supporting_evidence_ids=supporting_evidence_ids,
        alternative_explanations=[
            "External dependency degradation.",
            "Database or infrastructure contention.",
        ],
        next_steps=[
            "Compare behavior before and after the deployment.",
            "Inspect dependency and database telemetry.",
        ],
    )


# ---------------------------------------------------------------------------
# Valid result
# ---------------------------------------------------------------------------


def test_valid_investigation_result_is_accepted():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is True
    assert evaluation.errors == []
    assert evaluation.evidence_count == 1
    assert evaluation.supporting_evidence_count == 1
    assert evaluation.evidence_coverage == 1.0


# ---------------------------------------------------------------------------
# Missing supporting evidence
# ---------------------------------------------------------------------------


def test_result_without_supporting_evidence_is_rejected():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is False
    assert any(
        "supporting evidence" in error.lower()
        for error in evaluation.errors
    )


# ---------------------------------------------------------------------------
# Supporting evidence does not belong to context
# ---------------------------------------------------------------------------


def test_result_with_unknown_supporting_evidence_is_rejected():
    context_evidence = make_evidence()
    unknown_evidence_id = uuid4()

    context = make_context(
        evidence_items=[context_evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[unknown_evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is False
    assert any(
        "not present in the investigation context" in error
        for error in evaluation.errors
    )


# ---------------------------------------------------------------------------
# No evidence in context
# ---------------------------------------------------------------------------


def test_empty_evidence_context_is_rejected():
    context = make_context(
        evidence_items=[],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[uuid4()],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is False
    assert evaluation.evidence_count == 0
    assert any(
        "no evidence items" in error.lower()
        for error in evaluation.errors
    )


# ---------------------------------------------------------------------------
# Unsupported reasoning source
# ---------------------------------------------------------------------------


def test_unsupported_reasoning_source_is_rejected():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="unknown_source",
    )

    assert evaluation.is_valid is False
    assert any(
        "unsupported reasoning source" in error.lower()
        for error in evaluation.errors
    )


# ---------------------------------------------------------------------------
# Single evidence item produces warning
# ---------------------------------------------------------------------------


def test_single_supporting_evidence_produces_warning():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is True
    assert any(
        "only one evidence item" in warning.lower()
        for warning in evaluation.warnings
    )


# ---------------------------------------------------------------------------
# Missing timeline is a warning, not an error
# ---------------------------------------------------------------------------


def test_missing_timeline_is_warning_not_failure():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
        timeline_events=[],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is True
    assert any(
        "no timeline events" in warning.lower()
        for warning in evaluation.warnings
    )


# ---------------------------------------------------------------------------
# Missing historical incidents is a warning, not an error
# ---------------------------------------------------------------------------


def test_missing_historical_incidents_is_warning_not_failure():
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
        historical_incidents=[],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is True
    assert any(
        "no historical incidents" in warning.lower()
        for warning in evaluation.warnings
    )


# ---------------------------------------------------------------------------
# Evidence coverage
# ---------------------------------------------------------------------------


def test_evidence_coverage_is_calculated_correctly():
    evidence_one = make_evidence()
    evidence_two = make_evidence()
    evidence_three = make_evidence()
    evidence_four = make_evidence()

    context = make_context(
        evidence_items=[
            evidence_one,
            evidence_two,
            evidence_three,
            evidence_four,
        ],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[
            evidence_one.evidence_id,
            evidence_two.evidence_id,
        ],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source="ai",
    )

    assert evaluation.is_valid is True
    assert evaluation.evidence_count == 4
    assert evaluation.supporting_evidence_count == 2
    assert evaluation.evidence_coverage == 0.5


# ---------------------------------------------------------------------------
# Fallback provenance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reasoning_source",
    [
        "ai",
        "deterministic_fallback",
    ],
)
def test_supported_reasoning_sources_are_accepted(reasoning_source):
    evidence = make_evidence()

    context = make_context(
        evidence_items=[evidence],
    )

    hypothesis = make_hypothesis(
        supporting_evidence_ids=[evidence.evidence_id],
    )

    evaluation = evaluate_investigation_result(
        context=context,
        hypothesis=hypothesis,
        reasoning_source=reasoning_source,
    )

    assert evaluation.is_valid is True
    assert evaluation.errors == []