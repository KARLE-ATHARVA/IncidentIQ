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
        description="Checkout latency increased significantly.",
    )


def make_context(evidence_items):
    return SimpleNamespace(
        evidence_items=evidence_items,
        timeline_events=[SimpleNamespace()],
        historical_incidents=[SimpleNamespace()],
    )


def make_hypothesis(supporting_evidence_ids):
    return InvestigationHypothesis(
        hypothesis=(
            "A recent deployment may have contributed "
            "to the checkout latency incident."
        ),
        confidence=0.7,
        reasoning=(
            "The deployment occurred near the observed latency "
            "increase and is supported by the available telemetry."
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


def test_investigation_benchmark():
    # ---------------------------------------------------------
    # Case 1: Valid AI investigation
    # ---------------------------------------------------------
    evidence_one = make_evidence()

    valid_context = make_context(
        [evidence_one]
    )

    valid_hypothesis = make_hypothesis(
        [evidence_one.evidence_id]
    )

    valid_evaluation = evaluate_investigation_result(
        context=valid_context,
        hypothesis=valid_hypothesis,
        reasoning_source="ai",
    )

    # ---------------------------------------------------------
    # Case 2: Unknown evidence reference
    # ---------------------------------------------------------
    evidence_two = make_evidence()

    unknown_context = make_context(
        [evidence_two]
    )

    unknown_hypothesis = make_hypothesis(
        [uuid4()]
    )

    unknown_evaluation = evaluate_investigation_result(
        context=unknown_context,
        hypothesis=unknown_hypothesis,
        reasoning_source="ai",
    )

    # ---------------------------------------------------------
    # Case 3: Missing supporting evidence
    # ---------------------------------------------------------
    evidence_three = make_evidence()

    missing_context = make_context(
        [evidence_three]
    )

    missing_hypothesis = make_hypothesis(
        []
    )

    missing_evaluation = evaluate_investigation_result(
        context=missing_context,
        hypothesis=missing_hypothesis,
        reasoning_source="ai",
    )

    # ---------------------------------------------------------
    # Case 4: Deterministic fallback provenance
    # ---------------------------------------------------------
    evidence_four = make_evidence()

    fallback_context = make_context(
        [evidence_four]
    )

    fallback_hypothesis = make_hypothesis(
        [evidence_four.evidence_id]
    )

    fallback_evaluation = evaluate_investigation_result(
        context=fallback_context,
        hypothesis=fallback_hypothesis,
        reasoning_source="deterministic_fallback",
    )

    # ---------------------------------------------------------
    # Aggregate benchmark metrics
    # ---------------------------------------------------------
    evaluations = [
        valid_evaluation,
        unknown_evaluation,
        missing_evaluation,
        fallback_evaluation,
    ]

    total_cases = len(evaluations)

    valid_cases = sum(
        evaluation.is_valid
        for evaluation in evaluations
    )

    invalid_cases = total_cases - valid_cases

    grounded_cases = sum(
        not any(
            "not present in the investigation context"
            in error.lower()
            for error in evaluation.errors
        )
        for evaluation in evaluations
    )

    total_evidence = sum(
        evaluation.evidence_count
        for evaluation in evaluations
    )

    total_supporting_evidence = sum(
        evaluation.supporting_evidence_count
        for evaluation in evaluations
    )

    average_evidence_coverage = (
        sum(
            evaluation.evidence_coverage
            for evaluation in evaluations
        )
        / total_cases
    )

    grounding_rate = grounded_cases / total_cases

    # ---------------------------------------------------------
    # Benchmark report
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("INCIDENTIQ AI INVESTIGATION BENCHMARK")
    print("=" * 60)

    print(f"Total cases:              {total_cases}")
    print(f"Valid cases:              {valid_cases}")
    print(f"Invalid cases:            {invalid_cases}")
    print(f"Grounded cases:           {grounded_cases}")
    print(f"Grounding rate:            {grounding_rate:.3f}")
    print(f"Total evidence items:     {total_evidence}")
    print(f"Supporting evidence:      {total_supporting_evidence}")
    print(
        f"Average evidence coverage:"
        f" {average_evidence_coverage:.3f}"
    )

    print("=" * 60)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert total_cases == 4

    # Two valid cases:
    # 1. AI
    # 2. deterministic fallback
    assert valid_cases == 2

    assert invalid_cases == 2

    # Two cases do not contain unsupported evidence references:
    # 1. valid AI
    # 2. missing supporting evidence
    # 3. fallback
    #
    # The unknown-evidence case is the only explicit grounding
    # violation.
    assert grounded_cases == 3

    assert grounding_rate == 0.75

    assert total_evidence == 4

    assert total_supporting_evidence == 2

    assert average_evidence_coverage == 0.5

    # Explicitly verify the important cases.
    assert valid_evaluation.is_valid is True

    assert unknown_evaluation.is_valid is False

    assert missing_evaluation.is_valid is False

    assert fallback_evaluation.is_valid is True
