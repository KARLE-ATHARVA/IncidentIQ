from dataclasses import dataclass

from backend.app.services.correlation import CorrelationLevel, CorrelationResult


@dataclass(frozen=True)
class CorrelationEvaluationCase:
    result: CorrelationResult
    expected_correlated: bool


@dataclass(frozen=True)
class CorrelationEvaluation:
    total_cases: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float


def evaluate_correlation_results(
    cases: list[CorrelationEvaluationCase],
) -> CorrelationEvaluation:
    """
    Evaluate whether correlation results correctly identify
    expected relationships.

    A result is considered positively correlated when its
    correlation level is STRONG or VERY_STRONG.
    """

    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    for case in cases:
        predicted_correlated = case.result.correlation_level in {
            CorrelationLevel.STRONG,
            CorrelationLevel.VERY_STRONG,
        }

        if predicted_correlated and case.expected_correlated:
            true_positives += 1
        elif predicted_correlated and not case.expected_correlated:
            false_positives += 1
        elif not predicted_correlated and case.expected_correlated:
            false_negatives += 1
        else:
            true_negatives += 1

    total_cases = len(cases)

    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    accuracy_denominator = total_cases

    precision = (
        true_positives / precision_denominator
        if precision_denominator
        else 0.0
    )

    recall = (
        true_positives / recall_denominator
        if recall_denominator
        else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    accuracy = (
        (true_positives + true_negatives) / accuracy_denominator
        if accuracy_denominator
        else 0.0
    )

    return CorrelationEvaluation(
        total_cases=total_cases,
        true_positives=true_positives,
        false_positives=false_positives,
        true_negatives=true_negatives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        accuracy=accuracy,
    )
