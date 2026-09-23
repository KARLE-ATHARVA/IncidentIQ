from datetime import datetime, timedelta

from backend.app.services.correlation import (
    CorrelationLevel,
    CorrelationSignal,
    correlate_signals,
)
from backend.app.services.correlation_evaluation import (
    CorrelationEvaluationCase,
    evaluate_correlation_results,
)


def make_signal(
    *,
    service_id,
    signal_type,
    name,
    timestamp,
):
    from uuid import uuid4

    return CorrelationSignal(
        id=uuid4(),
        service_id=service_id,
        timestamp=timestamp,
        signal_type=signal_type,
        name=name,
    )


def run_benchmark():
    from uuid import uuid4

    base_time = datetime.now()
    service_a = uuid4()
    service_b = uuid4()

    cases = []

    # ---------------------------------------------------------
    # 1. Nearby metric anomaly + error log
    # Expected: strong correlation
    # ---------------------------------------------------------
    metric = make_signal(
        service_id=service_a,
        signal_type="metric_anomaly",
        name="checkout_latency",
        timestamp=base_time,
    )

    error_log = make_signal(
        service_id=service_a,
        signal_type="log_error",
        name="payment_timeout",
        timestamp=base_time + timedelta(seconds=30),
    )

    result = correlate_signals(metric, error_log)

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=True,
        )
    )

    # ---------------------------------------------------------
    # 2. Nearby metric anomaly + deployment
    # Expected: strong correlation
    # ---------------------------------------------------------
    deployment = make_signal(
        service_id=service_a,
        signal_type="deployment",
        name="checkout-v42",
        timestamp=base_time + timedelta(seconds=60),
    )

    result = correlate_signals(metric, deployment)

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=True,
        )
    )

    # ---------------------------------------------------------
    # 3. Nearby deployment + error log
    # Expected: strong correlation
    # ---------------------------------------------------------
    result = correlate_signals(
        deployment,
        error_log,
    )

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=True,
        )
    )

    # ---------------------------------------------------------
    # 4. Far-away metric anomaly + error log
    # Expected: not strongly correlated
    # ---------------------------------------------------------
    far_error = make_signal(
        service_id=service_a,
        signal_type="log_error",
        name="old_payment_timeout",
        timestamp=base_time + timedelta(seconds=600),
    )

    result = correlate_signals(
        metric,
        far_error,
    )

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=False,
        )
    )

    # ---------------------------------------------------------
    # 5. Different services
    # Expected: not strongly correlated
    # ---------------------------------------------------------
    unrelated_service_log = make_signal(
        service_id=service_b,
        signal_type="log_error",
        name="unrelated_service_error",
        timestamp=base_time + timedelta(seconds=30),
    )

    result = correlate_signals(
        metric,
        unrelated_service_log,
    )

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=False,
        )
    )

    # ---------------------------------------------------------
    # 6. Unknown signal types
    # Expected: not strongly correlated
    # ---------------------------------------------------------
    unknown_a = make_signal(
        service_id=service_a,
        signal_type="unknown",
        name="signal_a",
        timestamp=base_time,
    )

    unknown_b = make_signal(
        service_id=service_a,
        signal_type="unknown",
        name="signal_b",
        timestamp=base_time + timedelta(seconds=30),
    )

    result = correlate_signals(
        unknown_a,
        unknown_b,
    )

    cases.append(
        CorrelationEvaluationCase(
            result=result,
            expected_correlated=False,
        )
    )

    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------
    evaluation = evaluate_correlation_results(cases)

    print("\n" + "=" * 60)
    print("INCIDENTIQ CORRELATION BENCHMARK")
    print("=" * 60)
    print(f"Total cases:       {evaluation.total_cases}")
    print(f"True positives:    {evaluation.true_positives}")
    print(f"False positives:   {evaluation.false_positives}")
    print(f"True negatives:    {evaluation.true_negatives}")
    print(f"False negatives:   {evaluation.false_negatives}")
    print(f"Precision:         {evaluation.precision:.3f}")
    print(f"Recall:            {evaluation.recall:.3f}")
    print(f"F1 score:          {evaluation.f1_score:.3f}")
    print(f"Accuracy:          {evaluation.accuracy:.3f}")
    print("=" * 60)

    return evaluation


def test_real_correlation_benchmark():
    evaluation = run_benchmark()

    assert evaluation.total_cases == 6
    assert evaluation.true_positives == 3
    assert evaluation.false_positives == 0
    assert evaluation.true_negatives == 3
    assert evaluation.false_negatives == 0

    assert evaluation.precision == 1.0
    assert evaluation.recall == 1.0
    assert evaluation.f1_score == 1.0
    assert evaluation.accuracy == 1.0
