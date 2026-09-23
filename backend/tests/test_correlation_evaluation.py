from uuid import uuid4

import pytest

from backend.app.services.correlation import (
    CorrelationLevel,
    CorrelationResult,
)
from backend.app.services.correlation_evaluation import (
    CorrelationEvaluationCase,
    evaluate_correlation_results,
)


def make_result(level: CorrelationLevel) -> CorrelationResult:
    return CorrelationResult(
        related_signal_id=uuid4(),
        related_signal_type="log_error",
        related_signal_name="payment_timeout",
        correlation_score=0.9,
        correlation_level=level,
        temporal_score=1.0,
        service_score=1.0,
        telemetry_score=1.0,
        deployment_score=0.0,
        time_difference_seconds=30.0,
        same_service=True,
        deployment_nearby=False,
        reasons=["test correlation"],
    )


def test_perfect_correlation_evaluation():
    cases = [
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.STRONG),
            expected_correlated=True,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.VERY_STRONG),
            expected_correlated=True,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.MODERATE),
            expected_correlated=False,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.NONE),
            expected_correlated=False,
        ),
    ]

    evaluation = evaluate_correlation_results(cases)

    assert evaluation.total_cases == 4
    assert evaluation.true_positives == 2
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 2
    assert evaluation.false_negatives == 0
    assert evaluation.precision == pytest.approx(1.0)
    assert evaluation.recall == pytest.approx(1.0)
    assert evaluation.f1_score == pytest.approx(1.0)
    assert evaluation.accuracy == pytest.approx(1.0)


def test_false_positive():
    cases = [
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.STRONG),
            expected_correlated=False,
        ),
    ]

    evaluation = evaluate_correlation_results(cases)

    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 1
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 0
    assert evaluation.precision == pytest.approx(0.0)
    assert evaluation.recall == pytest.approx(0.0)
    assert evaluation.f1_score == pytest.approx(0.0)
    assert evaluation.accuracy == pytest.approx(0.0)


def test_false_negative():
    cases = [
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.MODERATE),
            expected_correlated=True,
        ),
    ]

    evaluation = evaluate_correlation_results(cases)

    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 1
    assert evaluation.precision == pytest.approx(0.0)
    assert evaluation.recall == pytest.approx(0.0)
    assert evaluation.f1_score == pytest.approx(0.0)
    assert evaluation.accuracy == pytest.approx(0.0)


def test_mixed_results():
    cases = [
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.STRONG),
            expected_correlated=True,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.VERY_STRONG),
            expected_correlated=True,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.STRONG),
            expected_correlated=False,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.MODERATE),
            expected_correlated=False,
        ),
        CorrelationEvaluationCase(
            result=make_result(CorrelationLevel.NONE),
            expected_correlated=True,
        ),
    ]

    evaluation = evaluate_correlation_results(cases)

    assert evaluation.total_cases == 5
    assert evaluation.true_positives == 2
    assert evaluation.false_positives == 1
    assert evaluation.true_negatives == 1
    assert evaluation.false_negatives == 1

    assert evaluation.precision == pytest.approx(2 / 3)
    assert evaluation.recall == pytest.approx(2 / 3)
    assert evaluation.f1_score == pytest.approx(2 / 3)
    assert evaluation.accuracy == pytest.approx(3 / 5)


def test_empty_cases_are_safe():
    evaluation = evaluate_correlation_results([])

    assert evaluation.total_cases == 0
    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 0
    assert evaluation.precision == 0.0
    assert evaluation.recall == 0.0
    assert evaluation.f1_score == 0.0
    assert evaluation.accuracy == 0.0
