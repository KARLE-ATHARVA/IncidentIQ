from dataclasses import dataclass
from uuid import UUID

from backend.app.services.detection import (
    AnomalyDetectionResult,
    DetectionStatus,
)


@dataclass(frozen=True)
class DetectionEvaluation:
    """
    Deterministic evaluation of anomaly detection results
    against known ground-truth labels.

    An anomaly is treated as the positive class.

    This evaluator measures classification behavior. It does
    not determine whether the underlying detection algorithm is
    scientifically correct beyond the supplied ground truth.
    """

    total_cases: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    insufficient_data_count: int

    precision: float
    recall: float
    f1_score: float
    accuracy: float


@dataclass(frozen=True)
class DetectionEvaluationCase:
    """
    One labeled detection evaluation case.

    expected_anomaly:
        Ground-truth label for the observation.

    result:
        Actual result produced by IncidentIQ's detection engine.
    """

    metric_event_id: UUID
    expected_anomaly: bool
    result: AnomalyDetectionResult


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def evaluate_detection_results(
    cases: list[DetectionEvaluationCase],
) -> DetectionEvaluation:
    """
    Evaluate anomaly detection results against ground truth.

    The positive class is ANOMALY.

    NORMAL:
        predicted negative

    ANOMALY:
        predicted positive

    INSUFFICIENT_DATA:
        excluded from TP/FP/TN/FN classification and counted
        separately.

    This makes insufficient historical data visible instead of
    incorrectly treating it as a normal prediction.
    """

    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    insufficient_data_count = 0

    for case in cases:
        status = case.result.status

        if status == DetectionStatus.INSUFFICIENT_DATA:
            insufficient_data_count += 1
            continue

        predicted_anomaly = status == DetectionStatus.ANOMALY

        if case.expected_anomaly and predicted_anomaly:
            true_positives += 1

        elif not case.expected_anomaly and predicted_anomaly:
            false_positives += 1

        elif not case.expected_anomaly and not predicted_anomaly:
            true_negatives += 1

        elif case.expected_anomaly and not predicted_anomaly:
            false_negatives += 1

    classified_cases = (
        true_positives
        + false_positives
        + true_negatives
        + false_negatives
    )

    precision = _safe_divide(
        true_positives,
        true_positives + false_positives,
    )

    recall = _safe_divide(
        true_positives,
        true_positives + false_negatives,
    )

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = (
            2 * precision * recall
            / (precision + recall)
        )

    accuracy = _safe_divide(
        true_positives + true_negatives,
        classified_cases,
    )

    return DetectionEvaluation(
        total_cases=len(cases),
        true_positives=true_positives,
        false_positives=false_positives,
        true_negatives=true_negatives,
        false_negatives=false_negatives,
        insufficient_data_count=insufficient_data_count,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        accuracy=accuracy,
    )
