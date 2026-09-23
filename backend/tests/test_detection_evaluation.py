from types import SimpleNamespace
from uuid import uuid4

from backend.app.services.detection import DetectionStatus
from backend.app.services.detection_evaluation import (
    DetectionEvaluationCase,
    evaluate_detection_results,
)


def make_result(status):
    return SimpleNamespace(
        metric_event_id=uuid4(),
        status=status,
    )


def make_case(expected_anomaly, status):
    result = make_result(status)

    return DetectionEvaluationCase(
        metric_event_id=result.metric_event_id,
        expected_anomaly=expected_anomaly,
        result=result,
    )


def test_perfect_detection():

    cases = [
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.ANOMALY,
        ),
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.ANOMALY,
        ),
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.NORMAL,
        ),
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.NORMAL,
        ),
    ]

    evaluation = evaluate_detection_results(cases)

    assert evaluation.total_cases == 4

    assert evaluation.true_positives == 2
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 2
    assert evaluation.false_negatives == 0

    assert evaluation.precision == 1.0
    assert evaluation.recall == 1.0
    assert evaluation.f1_score == 1.0
    assert evaluation.accuracy == 1.0


def test_false_positive_is_counted():

    cases = [
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.ANOMALY,
        ),
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.ANOMALY,
        ),
    ]

    evaluation = evaluate_detection_results(cases)

    assert evaluation.true_positives == 1
    assert evaluation.false_positives == 1
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 0

    assert evaluation.precision == 0.5
    assert evaluation.recall == 1.0


def test_false_negative_is_counted():

    cases = [
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.NORMAL,
        ),
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.NORMAL,
        ),
    ]

    evaluation = evaluate_detection_results(cases)

    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 1
    assert evaluation.false_negatives == 1

    assert evaluation.precision == 0.0
    assert evaluation.recall == 0.0
    assert evaluation.f1_score == 0.0


def test_insufficient_data_is_tracked_separately():

    cases = [
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.INSUFFICIENT_DATA,
        ),
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.INSUFFICIENT_DATA,
        ),
    ]

    evaluation = evaluate_detection_results(cases)

    assert evaluation.total_cases == 2

    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 0

    assert evaluation.insufficient_data_count == 2

    assert evaluation.precision == 0.0
    assert evaluation.recall == 0.0
    assert evaluation.f1_score == 0.0
    assert evaluation.accuracy == 0.0


def test_mixed_detection_results():

    cases = [
        # TP
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.ANOMALY,
        ),

        # FN
        make_case(
            expected_anomaly=True,
            status=DetectionStatus.NORMAL,
        ),

        # FP
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.ANOMALY,
        ),

        # TN
        make_case(
            expected_anomaly=False,
            status=DetectionStatus.NORMAL,
        ),
    ]

    evaluation = evaluate_detection_results(cases)

    assert evaluation.total_cases == 4

    assert evaluation.true_positives == 1
    assert evaluation.false_positives == 1
    assert evaluation.true_negatives == 1
    assert evaluation.false_negatives == 1

    assert evaluation.precision == 0.5
    assert evaluation.recall == 0.5
    assert evaluation.f1_score == 0.5
    assert evaluation.accuracy == 0.5


def test_empty_evaluation_is_safe():

    evaluation = evaluate_detection_results([])

    assert evaluation.total_cases == 0

    assert evaluation.true_positives == 0
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 0
    assert evaluation.false_negatives == 0

    assert evaluation.insufficient_data_count == 0

    assert evaluation.precision == 0.0
    assert evaluation.recall == 0.0
    assert evaluation.f1_score == 0.0
    assert evaluation.accuracy == 0.0
