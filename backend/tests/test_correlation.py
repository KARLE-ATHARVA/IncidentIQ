from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.services.correlation import (
    CorrelationConfig,
    CorrelationLevel,
    CorrelationSignal,
    correlate_signals,
)


def make_signal(
    *,
    signal_type: str,
    name: str,
    service_id=None,
    timestamp=None,
):
    return CorrelationSignal(
        id=uuid4(),
        service_id=service_id or uuid4(),
        timestamp=timestamp or datetime.now(),
        signal_type=signal_type,
        name=name,
    )


def test_same_service_close_metric_anomaly_and_error_log():
    service_id = uuid4()
    timestamp = datetime.now()

    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
        service_id=service_id,
        timestamp=timestamp,
    )

    log = make_signal(
        signal_type="log_error",
        name="payment_timeout",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=30),
    )

    result = correlate_signals(metric, log)

    assert result.same_service is True
    assert result.temporal_score > 0
    assert result.telemetry_score == 1.0
    assert result.correlation_score > 0.70
    assert result.correlation_level in {
        CorrelationLevel.STRONG,
        CorrelationLevel.VERY_STRONG,
    }


def test_same_service_farther_apart_has_lower_temporal_score():
    service_id = uuid4()
    timestamp = datetime.now()

    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
        service_id=service_id,
        timestamp=timestamp,
    )

    log = make_signal(
        signal_type="log_error",
        name="payment_timeout",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=240),
    )

    result = correlate_signals(metric, log)

    assert result.same_service is True
    assert result.temporal_score > 0
    assert result.temporal_score < 0.5
    assert result.correlation_score < 0.70


def test_different_services_reduce_correlation():
    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
    )

    log = make_signal(
        signal_type="log_error",
        name="payment_timeout",
    )

    result = correlate_signals(metric, log)

    assert result.same_service is False
    assert result.service_score == 0.0
    assert result.telemetry_score == 1.0
    assert result.correlation_score < 0.75


def test_metric_anomaly_and_deployment_have_telemetry_relationship():
    service_id = uuid4()
    timestamp = datetime.now()

    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
        service_id=service_id,
        timestamp=timestamp,
    )

    deployment = make_signal(
        signal_type="deployment",
        name="checkout-v42",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=60),
    )

    result = correlate_signals(metric, deployment)

    assert result.same_service is True
    assert result.deployment_nearby is True
    assert result.telemetry_score == 1.0
    assert result.deployment_score > 0
    assert result.correlation_score > 0.70


def test_deployment_outside_window_is_not_nearby():
    service_id = uuid4()
    timestamp = datetime.now()

    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
        service_id=service_id,
        timestamp=timestamp,
    )

    deployment = make_signal(
        signal_type="deployment",
        name="checkout-v42",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=600),
    )

    result = correlate_signals(metric, deployment)

    assert result.temporal_score == 0.0
    assert result.deployment_nearby is False


def test_completely_unrelated_signal_types_have_no_telemetry_relationship():
    service_id = uuid4()
    timestamp = datetime.now()

    signal_a = make_signal(
        signal_type="unknown",
        name="signal_a",
        service_id=service_id,
        timestamp=timestamp,
    )

    signal_b = make_signal(
        signal_type="unknown",
        name="signal_b",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=30),
    )

    result = correlate_signals(signal_a, signal_b)

    assert result.telemetry_score == 0.0
    assert result.correlation_score < 0.70


def test_signals_outside_correlation_window_have_zero_temporal_score():
    config = CorrelationConfig(
        correlation_window_seconds=300.0,
    )

    timestamp = datetime.now()

    signal_a = make_signal(
        signal_type="metric_anomaly",
        name="latency",
        timestamp=timestamp,
    )

    signal_b = make_signal(
        signal_type="log_error",
        name="error",
        timestamp=timestamp + timedelta(seconds=301),
    )

    result = correlate_signals(
        signal_a,
        signal_b,
        config=config,
    )

    assert result.time_difference_seconds == pytest.approx(301.0)
    assert result.temporal_score == 0.0


def test_correlation_is_symmetric():
    service_id = uuid4()
    timestamp = datetime.now()

    metric = make_signal(
        signal_type="metric_anomaly",
        name="checkout_latency",
        service_id=service_id,
        timestamp=timestamp,
    )

    log = make_signal(
        signal_type="log_error",
        name="payment_timeout",
        service_id=service_id,
        timestamp=timestamp + timedelta(seconds=30),
    )

    result_ab = correlate_signals(metric, log)
    result_ba = correlate_signals(log, metric)

    assert result_ab.correlation_score == pytest.approx(
        result_ba.correlation_score
    )

    assert result_ab.temporal_score == pytest.approx(
        result_ba.temporal_score
    )

    assert result_ab.service_score == pytest.approx(
        result_ba.service_score
    )

    assert result_ab.telemetry_score == pytest.approx(
        result_ba.telemetry_score
    )


def test_invalid_correlation_window_is_rejected():
    with pytest.raises(ValueError):
        CorrelationConfig(
            correlation_window_seconds=0,
        )


def test_invalid_weights_are_rejected():
    config = CorrelationConfig(
        temporal_weight=0.5,
        service_weight=0.5,
        telemetry_weight=0.5,
        deployment_weight=0.5,
    )

    with pytest.raises(ValueError):
        correlate_signals(
            make_signal(
                signal_type="metric_anomaly",
                name="latency",
            ),
            make_signal(
                signal_type="log_error",
                name="error",
            ),
            config=config,
        )


def test_invalid_threshold_order_is_rejected():
    config = CorrelationConfig(
        weak_threshold=0.8,
        moderate_threshold=0.5,
        strong_threshold=0.7,
        very_strong_threshold=0.9,
    )

    with pytest.raises(ValueError):
        correlate_signals(
            make_signal(
                signal_type="metric_anomaly",
                name="latency",
            ),
            make_signal(
                signal_type="log_error",
                name="error",
            ),
            config=config,
        )