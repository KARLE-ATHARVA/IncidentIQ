from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.services.detection import (
    DetectionConfig,
    DetectionDirection,
    DetectionStatus,
    calculate_mad,
    calculate_percentage_deviation,
    calculate_robust_z_score,
    calculate_z_score,
    detect_anomaly,
    determine_direction,
)


def make_detection_kwargs():
    return {
        "service_id": uuid4(),
        "metric_event_id": uuid4(),
        "metric_name": "checkout_latency",
        "observed_at": datetime.now(timezone.utc),
    }


def test_calculate_percentage_deviation():
    assert calculate_percentage_deviation(120.0, 100.0) == 20.0
    assert calculate_percentage_deviation(80.0, 100.0) == -20.0


def test_calculate_percentage_deviation_with_zero_baseline():
    assert calculate_percentage_deviation(100.0, 0.0) is None


def test_calculate_z_score():
    assert calculate_z_score(110.0, 100.0, 5.0) == 2.0


def test_calculate_z_score_with_zero_standard_deviation():
    assert calculate_z_score(110.0, 100.0, 0.0) is None


def test_calculate_mad():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]

    assert calculate_mad(values, 3.0) == 1.0


def test_calculate_robust_z_score():
    result = calculate_robust_z_score(
        current_value=105.0,
        median_value=100.0,
        mad=2.0,
    )

    assert result == pytest.approx(1.68625)


def test_calculate_robust_z_score_with_zero_mad():
    assert calculate_robust_z_score(105.0, 100.0, 0.0) is None


def test_determine_direction_above():
    assert determine_direction(110.0, 100.0) == DetectionDirection.ABOVE


def test_determine_direction_below():
    assert determine_direction(90.0, 100.0) == DetectionDirection.BELOW


def test_determine_direction_normal():
    assert determine_direction(100.0, 100.0) == DetectionDirection.NORMAL


def test_detect_anomaly_with_insufficient_historical_data():
    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=150.0,
        historical_values=[100.0, 101.0, 99.0],
        recent_values=[],
        config=DetectionConfig(minimum_observations=10),
    )

    assert result.status == DetectionStatus.INSUFFICIENT_DATA
    assert result.baseline_value is None
    assert result.standard_deviation is None
    assert result.median is None
    assert result.mad is None
    assert result.z_score is None
    assert result.robust_z_score is None
    assert result.percentage_deviation is None
    assert result.direction == DetectionDirection.NORMAL
    assert result.detection_method is None
    assert result.anomalous_observations == 0


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (
            DetectionConfig(minimum_observations=0),
            "minimum_observations must be at least 1",
        ),
        (
            DetectionConfig(persistence_window=0),
            "persistence_window must be at least 1",
        ),
        (
            DetectionConfig(minimum_anomalous_observations=0),
            "minimum_anomalous_observations must be at least 1",
        ),
        (
            DetectionConfig(
                persistence_window=2,
                minimum_anomalous_observations=4,
            ),
            "minimum_anomalous_observations cannot exceed persistence_window + 1",
        ),
        (
            DetectionConfig(z_score_threshold=0),
            "z_score_threshold must be greater than 0",
        ),
        (
            DetectionConfig(robust_z_score_threshold=0),
            "robust_z_score_threshold must be greater than 0",
        ),
    ],
)
def test_detect_anomaly_validates_configuration(config, message):
    with pytest.raises(ValueError, match=message):
        detect_anomaly(
            **make_detection_kwargs(),
            current_value=100.0,
            historical_values=[100.0] * 10,
            recent_values=[100.0] * 5,
            config=config,
        )


def test_detect_anomaly_returns_normal_when_value_is_within_expected_range():
    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=100.0,
        historical_values=[
            98.0,
            99.0,
            100.0,
            101.0,
            102.0,
            99.0,
            100.0,
            101.0,
            98.0,
            102.0,
        ],
        recent_values=[
            100.0,
            101.0,
            99.0,
            100.0,
            101.0,
        ],
    )

    assert result.status == DetectionStatus.NORMAL
    assert result.detection_method is None
    assert result.direction == DetectionDirection.NORMAL
    assert result.anomalous_observations == 0
    assert "within the expected range" in result.explanation


def test_detect_anomaly_returns_transient_anomaly_when_persistence_is_not_satisfied():
    historical_values = [
        98.0,
        99.0,
        100.0,
        101.0,
        102.0,
        99.0,
        100.0,
        101.0,
        98.0,
        102.0,
        100.0,
        99.0,
        101.0,
        100.0,
        98.0,
        102.0,
        100.0,
        101.0,
        99.0,
        100.0,
    ]

    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=180.0,
        historical_values=historical_values,
        recent_values=[100.0, 101.0, 99.0, 100.0, 101.0],
        config=DetectionConfig(
            persistence_window=5,
            minimum_anomalous_observations=3,
        ),
    )

    assert result.status == DetectionStatus.NORMAL
    assert result.detection_method == "transient_anomaly"
    assert result.anomalous_observations == 1
    assert "persistence requirement was not satisfied" in result.explanation


def test_detect_anomaly_handles_zero_variance():
    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=120.0,
        historical_values=[100.0] * 10,
        recent_values=[120.0, 120.0, 120.0],
        config=DetectionConfig(
            persistence_window=3,
            minimum_anomalous_observations=3,
        ),
    )

    assert result.status == DetectionStatus.ANOMALY
    assert result.standard_deviation == 0.0
    assert result.z_score is None
    assert result.detection_method == "zero_variance"
    assert result.direction == DetectionDirection.ABOVE
    assert result.anomalous_observations == 4
    assert result.explanation.startswith("Metric 'checkout_latency' is anomalous.")


def test_detect_anomaly_handles_zero_mad():
    historical_values = [100.0] * 8 + [101.0, 102.0]

    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=101.0,
        historical_values=historical_values,
        recent_values=[101.0, 101.0, 101.0],
        config=DetectionConfig(
            z_score_threshold=100.0,
            robust_z_score_threshold=100.0,
            persistence_window=3,
            minimum_anomalous_observations=3,
        ),
    )

    assert result.status == DetectionStatus.ANOMALY
    assert result.mad == 0.0
    assert result.robust_z_score is None
    assert result.detection_method == "zero_mad"
    assert result.anomalous_observations == 4


def test_detect_anomaly_uses_both_statistical_detection_methods():
    historical_values = [
        98.0,
        99.0,
        100.0,
        101.0,
        102.0,
        99.0,
        100.0,
        101.0,
        98.0,
        102.0,
        100.0,
        99.0,
        101.0,
        100.0,
        98.0,
        102.0,
        100.0,
        101.0,
        99.0,
        100.0,
    ]

    result = detect_anomaly(
        **make_detection_kwargs(),
        current_value=180.0,
        historical_values=historical_values,
        recent_values=[180.0, 181.0, 179.0, 182.0, 180.0],
    )

    assert result.status == DetectionStatus.ANOMALY
    assert "z_score" in result.detection_method
    assert "robust_z_score" in result.detection_method
    assert result.anomalous_observations >= 3
    assert result.z_score is not None
    assert result.robust_z_score is not None
    assert result.percentage_deviation is not None