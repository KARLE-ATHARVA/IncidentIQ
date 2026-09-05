from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from statistics import mean, median, pstdev
from uuid import UUID


class DetectionStatus(str, Enum):
    NORMAL = "normal"
    ANOMALY = "anomaly"
    INSUFFICIENT_DATA = "insufficient_data"


class DetectionDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    NORMAL = "normal"


@dataclass
class DetectionConfig:
    minimum_observations: int = 10
    z_score_threshold: float = 3.0
    robust_z_score_threshold: float = 3.5
    persistence_window: int = 5
    minimum_anomalous_observations: int = 3


@dataclass
class AnomalyDetectionResult:
    service_id: UUID
    metric_event_id: UUID
    metric_name: str

    current_value: float
    observed_at: datetime
    detected_at: datetime

    baseline_value: float | None
    standard_deviation: float | None
    median: float | None
    mad: float | None

    z_score: float | None
    robust_z_score: float | None
    percentage_deviation: float | None

    direction: DetectionDirection
    detection_method: str | None

    persistence_window: int
    anomalous_observations: int

    status: DetectionStatus
    explanation: str


def calculate_percentage_deviation(
    current_value: float,
    baseline_value: float,
) -> float | None:
    """
    Calculate how far the current value is from the baseline
    as a percentage.

    Returns None when the baseline is zero because percentage
    deviation would be undefined.
    """
    if baseline_value == 0:
        return None

    return (
        (current_value - baseline_value)
        / abs(baseline_value)
    ) * 100


def calculate_z_score(
    current_value: float,
    baseline_value: float,
    standard_deviation: float,
) -> float | None:
    """
    Calculate the standard z-score.

    Returns None when standard deviation is zero because
    division by zero is undefined.
    """
    if standard_deviation == 0:
        return None

    return (
        current_value - baseline_value
    ) / standard_deviation


def calculate_mad(
    values: list[float],
    median_value: float,
) -> float:
    """
    Calculate Median Absolute Deviation (MAD).

    MAD is more resistant to extreme outliers than
    standard deviation.
    """
    deviations = [
        abs(value - median_value)
        for value in values
    ]

    return median(deviations)


def calculate_robust_z_score(
    current_value: float,
    median_value: float,
    mad: float,
) -> float | None:
    """
    Calculate a robust z-score using Median Absolute Deviation.

    The 0.6745 scaling factor makes the score comparable
    to a standard z-score under a normal distribution.

    Returns None when MAD is zero.
    """
    if mad == 0:
        return None

    return (
        0.6745
        * (current_value - median_value)
        / mad
    )


def determine_direction(
    current_value: float,
    baseline_value: float,
) -> DetectionDirection:
    """
    Determine whether the current value is above, below,
    or equal to the baseline.
    """
    if current_value > baseline_value:
        return DetectionDirection.ABOVE

    if current_value < baseline_value:
        return DetectionDirection.BELOW

    return DetectionDirection.NORMAL


def detect_anomaly(
    service_id: UUID,
    metric_event_id: UUID,
    metric_name: str,
    current_value: float,
    observed_at: datetime,
    historical_values: list[float],
    recent_values: list[float],
    config: DetectionConfig | None = None,
) -> AnomalyDetectionResult:
    """
    Detect whether the current metric value is anomalous
    compared with historical observations.

    historical_values:
        Observations used to establish the normal baseline.

    recent_values:
        Most recent observations used to determine whether
        anomalous behavior is persistent.

    This function contains only detection logic.
    It does not access the database or external services.
    """

    if config is None:
        config = DetectionConfig()

    detected_at = datetime.now(observed_at.tzinfo)

    # ---------------------------------------------------------
    # 1. Validate detection configuration
    # ---------------------------------------------------------

    if config.minimum_observations < 1:
        raise ValueError(
            "minimum_observations must be at least 1"
        )

    if config.persistence_window < 1:
        raise ValueError(
            "persistence_window must be at least 1"
        )

    if config.minimum_anomalous_observations < 1:
        raise ValueError(
            "minimum_anomalous_observations must be at least 1"
        )

    if (
        config.minimum_anomalous_observations
        > config.persistence_window + 1
    ):
        raise ValueError(
            "minimum_anomalous_observations cannot exceed "
            "persistence_window + 1"
        )

    if config.z_score_threshold <= 0:
        raise ValueError(
            "z_score_threshold must be greater than 0"
        )

    if config.robust_z_score_threshold <= 0:
        raise ValueError(
            "robust_z_score_threshold must be greater than 0"
        )

    # ---------------------------------------------------------
    # 2. Check whether we have enough historical observations
    # ---------------------------------------------------------

    if len(historical_values) < config.minimum_observations:
        return AnomalyDetectionResult(
            service_id=service_id,
            metric_event_id=metric_event_id,
            metric_name=metric_name,
            current_value=current_value,
            observed_at=observed_at,
            detected_at=detected_at,
            baseline_value=None,
            standard_deviation=None,
            median=None,
            mad=None,
            z_score=None,
            robust_z_score=None,
            percentage_deviation=None,
            direction=DetectionDirection.NORMAL,
            detection_method=None,
            persistence_window=config.persistence_window,
            anomalous_observations=0,
            status=DetectionStatus.INSUFFICIENT_DATA,
            explanation=(
                f"Insufficient historical data for metric "
                f"'{metric_name}'. Required at least "
                f"{config.minimum_observations} observations, "
                f"but received {len(historical_values)}."
            ),
        )

    # ---------------------------------------------------------
    # 3. Calculate baseline statistics
    # ---------------------------------------------------------

    baseline_value = mean(historical_values)

    standard_deviation = pstdev(historical_values)

    median_value = median(historical_values)

    mad_value = calculate_mad(
        historical_values,
        median_value,
    )

    # ---------------------------------------------------------
    # 4. Calculate current observation scores
    # ---------------------------------------------------------

    z_score = calculate_z_score(
        current_value,
        baseline_value,
        standard_deviation,
    )

    robust_z_score = calculate_robust_z_score(
        current_value,
        median_value,
        mad_value,
    )

    percentage_deviation = calculate_percentage_deviation(
        current_value,
        baseline_value,
    )

    direction = determine_direction(
        current_value,
        baseline_value,
    )

    # ---------------------------------------------------------
    # 5. Determine current statistical anomaly
    # ---------------------------------------------------------

    standard_anomaly = (
        z_score is not None
        and abs(z_score) >= config.z_score_threshold
    )

    robust_anomaly = (
        robust_z_score is not None
        and abs(robust_z_score)
        >= config.robust_z_score_threshold
    )

    # ---------------------------------------------------------
    # 6. Handle zero-variance / zero-MAD situations
    # ---------------------------------------------------------

    zero_variance_anomaly = (
        standard_deviation == 0
        and current_value != baseline_value
    )

    zero_mad_anomaly = (
        mad_value == 0
        and current_value != median_value
    )

    current_is_anomalous = (
        standard_anomaly
        or robust_anomaly
        or zero_variance_anomaly
        or zero_mad_anomaly
    )

    # ---------------------------------------------------------
    # 7. Determine persistence from recent observations
    # ---------------------------------------------------------

    persistence_values = recent_values[
        -config.persistence_window:
    ]

    anomalous_observations = 0

    for value in persistence_values:

        value_z_score = calculate_z_score(
            value,
            baseline_value,
            standard_deviation,
        )

        value_robust_z_score = calculate_robust_z_score(
            value,
            median_value,
            mad_value,
        )

        value_standard_anomaly = (
            value_z_score is not None
            and abs(value_z_score)
            >= config.z_score_threshold
        )

        value_robust_anomaly = (
            value_robust_z_score is not None
            and abs(value_robust_z_score)
            >= config.robust_z_score_threshold
        )

        value_zero_variance_anomaly = (
            standard_deviation == 0
            and value != baseline_value
        )

        value_zero_mad_anomaly = (
            mad_value == 0
            and value != median_value
        )

        value_is_anomalous = (
            value_standard_anomaly
            or value_robust_anomaly
            or value_zero_variance_anomaly
            or value_zero_mad_anomaly
        )

        if value_is_anomalous:
            anomalous_observations += 1

    # The current observation is separate from recent_values.
    if current_is_anomalous:
        anomalous_observations += 1

    persistence_satisfied = (
        anomalous_observations
        >= config.minimum_anomalous_observations
    )

    # ---------------------------------------------------------
    # 8. Determine detection method
    # ---------------------------------------------------------

    detection_methods = []

    if standard_anomaly:
        detection_methods.append("z_score")

    if robust_anomaly:
        detection_methods.append("robust_z_score")

    if zero_variance_anomaly:
        detection_methods.append("zero_variance")

    if zero_mad_anomaly:
        detection_methods.append("zero_mad")

    # ---------------------------------------------------------
    # 9. Final detection decision
    # ---------------------------------------------------------

    if current_is_anomalous and persistence_satisfied:

        status = DetectionStatus.ANOMALY

        detection_method = "+".join(
            detection_methods
        )

        if not detection_method:
            detection_method = "statistical"

        if z_score is not None:
            explanation = (
                f"Metric '{metric_name}' is anomalous. "
                f"Current value {current_value:.2f} is "
                f"{direction.value} the baseline "
                f"{baseline_value:.2f}. "
                f"Z-score: {z_score:.2f}. "
                f"{anomalous_observations} anomalous observations "
                f"were detected within the persistence window."
            )
        else:
            explanation = (
                f"Metric '{metric_name}' is anomalous. "
                f"Current value {current_value:.2f} is "
                f"{direction.value} the baseline "
                f"{baseline_value:.2f}. "
                f"{anomalous_observations} anomalous observations "
                f"were detected within the persistence window."
            )

    elif current_is_anomalous:

        status = DetectionStatus.NORMAL

        detection_method = "transient_anomaly"

        explanation = (
            f"Metric '{metric_name}' showed an unusual value, "
            f"but the persistence requirement was not satisfied. "
            f"{anomalous_observations} anomalous observations "
            f"were found; "
            f"{config.minimum_anomalous_observations} are required."
        )

    else:

        status = DetectionStatus.NORMAL

        detection_method = None

        explanation = (
            f"Metric '{metric_name}' is within the expected range. "
            f"Current value {current_value:.2f}, "
            f"baseline {baseline_value:.2f}."
        )

    # ---------------------------------------------------------
    # 10. Return structured detection evidence
    # ---------------------------------------------------------

    return AnomalyDetectionResult(
        service_id=service_id,
        metric_event_id=metric_event_id,
        metric_name=metric_name,
        current_value=current_value,
        observed_at=observed_at,
        detected_at=detected_at,
        baseline_value=baseline_value,
        standard_deviation=standard_deviation,
        median=median_value,
        mad=mad_value,
        z_score=z_score,
        robust_z_score=robust_z_score,
        percentage_deviation=percentage_deviation,
        direction=direction,
        detection_method=detection_method,
        persistence_window=config.persistence_window,
        anomalous_observations=anomalous_observations,
        status=status,
        explanation=explanation,
    )