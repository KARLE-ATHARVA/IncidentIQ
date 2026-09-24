from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.detection import (
    DetectionConfig,
    DetectionStatus,
    detect_anomaly,
)
from backend.app.services.detection_evaluation import (
    DetectionEvaluationCase,
    evaluate_detection_results,
)


def make_detection_case(
    *,
    historical_values: list[float],
    recent_values: list[float],
    current_value: float,
    expected_anomaly: bool,
):
    result = detect_anomaly(
        service_id=uuid4(),
        metric_event_id=uuid4(),
        metric_name="checkout_latency",
        current_value=current_value,
        observed_at=datetime.now(timezone.utc),
        historical_values=historical_values,
        recent_values=recent_values,
        config=DetectionConfig(
            minimum_observations=10,
            z_score_threshold=3.0,
            robust_z_score_threshold=3.5,
            persistence_window=5,
            minimum_anomalous_observations=3,
        ),
    )

    return DetectionEvaluationCase(
        metric_event_id=result.metric_event_id,
        expected_anomaly=expected_anomaly,
        result=result,
    )


def test_real_detection_benchmark():
    normal_history = [100.0] * 20

    anomaly_history = [
        100.0,
        101.0,
        99.0,
        100.0,
        102.0,
        98.0,
        101.0,
        99.0,
        100.0,
        101.0,
        99.0,
        100.0,
        102.0,
        98.0,
        100.0,
        101.0,
        99.0,
        100.0,
        101.0,
        99.0,
    ]

    cases = []

    # ---------------------------------------------------------
    # True positives
    # ---------------------------------------------------------

    for _ in range(5):
        cases.append(
            make_detection_case(
                historical_values=anomaly_history,
                recent_values=[180.0, 181.0, 179.0, 182.0, 180.0],
                current_value=180.0,
                expected_anomaly=True,
            )
        )

    # ---------------------------------------------------------
    # True negatives
    # ---------------------------------------------------------

    for _ in range(5):
        cases.append(
            make_detection_case(
                historical_values=anomaly_history,
                recent_values=[100.0, 101.0, 99.0, 100.0, 101.0],
                current_value=100.0,
                expected_anomaly=False,
            )
        )

    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------

    evaluation = evaluate_detection_results(cases)

    print("\n" + "=" * 60)
    print("INCIDENTIQ DETECTION BENCHMARK")
    print("=" * 60)
    print(f"Total cases:        {evaluation.total_cases}")
    print(f"True positives:     {evaluation.true_positives}")
    print(f"False positives:    {evaluation.false_positives}")
    print(f"True negatives:     {evaluation.true_negatives}")
    print(f"False negatives:    {evaluation.false_negatives}")
    print(
        f"Insufficient data:  "
        f"{evaluation.insufficient_data_count}"
    )
    print(f"Precision:          {evaluation.precision:.3f}")
    print(f"Recall:             {evaluation.recall:.3f}")
    print(f"F1 score:           {evaluation.f1_score:.3f}")
    print(f"Accuracy:           {evaluation.accuracy:.3f}")
    print("=" * 60)

    # ---------------------------------------------------------
    # Benchmark assertions
    # ---------------------------------------------------------

    assert evaluation.total_cases == 10

    assert evaluation.true_positives == 5
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 5
    assert evaluation.false_negatives == 0

    assert evaluation.insufficient_data_count == 0

    assert evaluation.precision == 1.0
    assert evaluation.recall == 1.0
    assert evaluation.f1_score == 1.0
    assert evaluation.accuracy == 1.0