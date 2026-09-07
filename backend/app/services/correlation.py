from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


# =========================================================
# ENUMS
# =========================================================


class CorrelationLevel(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


# =========================================================
# CONFIGURATION
# =========================================================


@dataclass(frozen=True)
class CorrelationConfig:
    """
    Configuration for the correlation engine.

    All scoring behavior is configurable so that the
    correlation logic does not depend on hard-coded values.
    """

    correlation_window_seconds: float = 300.0

    temporal_weight: float = 0.30
    service_weight: float = 0.25
    telemetry_weight: float = 0.20
    deployment_weight: float = 0.25

    weak_threshold: float = 0.30
    moderate_threshold: float = 0.50
    strong_threshold: float = 0.70
    very_strong_threshold: float = 0.85

    def __post_init__(self) -> None:
        if self.correlation_window_seconds <= 0:
            raise ValueError(
                "correlation_window_seconds must be greater than 0"
            )


# =========================================================
# CORRELATION SIGNAL
# =========================================================


@dataclass(frozen=True)
class CorrelationSignal:
    """
    Common representation of a signal that can participate
    in correlation.

    The correlation engine does not need to know whether
    the original object came from a metric, log, or
    deployment table.
    """

    id: UUID
    service_id: UUID
    timestamp: datetime
    signal_type: str
    name: str


# =========================================================
# CORRELATION RESULT
# =========================================================


@dataclass(frozen=True)
class CorrelationResult:
    """
    Structured explanation of the relationship between
    two signals.

    The related signal identity is preserved so downstream
    incident formation can trace correlation evidence back
    to the original telemetry event.
    """

    related_signal_id: UUID
    related_signal_type: str
    related_signal_name: str

    correlation_score: float
    correlation_level: CorrelationLevel

    temporal_score: float
    service_score: float
    telemetry_score: float
    deployment_score: float

    time_difference_seconds: float

    same_service: bool
    deployment_nearby: bool

    reasons: list[str]


# =========================================================
# VALIDATION
# =========================================================


def _validate_config(config: CorrelationConfig) -> None:
    """
    Validate correlation configuration.
    """

    if config.correlation_window_seconds <= 0:
        raise ValueError(
            "correlation_window_seconds must be greater than 0"
        )

    weights = [
        config.temporal_weight,
        config.service_weight,
        config.telemetry_weight,
        config.deployment_weight,
    ]

    if any(weight < 0 for weight in weights):
        raise ValueError(
            "Correlation weights cannot be negative"
        )

    total_weight = sum(weights)

    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            "Correlation weights must sum to 1.0"
        )

    thresholds = [
        config.weak_threshold,
        config.moderate_threshold,
        config.strong_threshold,
        config.very_strong_threshold,
    ]

    if any(
        threshold < 0 or threshold > 1
        for threshold in thresholds
    ):
        raise ValueError(
            "Correlation thresholds must be between 0 and 1"
        )

    if not (
        config.weak_threshold
        <= config.moderate_threshold
        <= config.strong_threshold
        <= config.very_strong_threshold
    ):
        raise ValueError(
            "Correlation thresholds must be in ascending order"
        )


# =========================================================
# TEMPORAL SCORE
# =========================================================


def _calculate_temporal_score(
    time_difference_seconds: float,
    correlation_window_seconds: float,
) -> float:
    """
    Calculate temporal proximity.

    Same timestamp:
        1.0

    At correlation window:
        0.0

    Outside correlation window:
        0.0
    """

    if time_difference_seconds < 0:
        raise ValueError(
            "time_difference_seconds cannot be negative"
        )

    if time_difference_seconds >= correlation_window_seconds:
        return 0.0

    score = (
        1.0
        - (
            time_difference_seconds
            / correlation_window_seconds
        )
    )

    return max(0.0, min(1.0, score))


# =========================================================
# SERVICE SCORE
# =========================================================


def _calculate_service_score(
    first_signal: CorrelationSignal,
    second_signal: CorrelationSignal,
) -> float:
    """
    Same service receives full service-correlation credit.
    """

    if first_signal.service_id == second_signal.service_id:
        return 1.0

    return 0.0


# =========================================================
# TELEMETRY RELATIONSHIP SCORE
# =========================================================


def _calculate_telemetry_score(
    first_signal: CorrelationSignal,
    second_signal: CorrelationSignal,
) -> float:
    """
    Determine how strongly the two signal types are related.
    """

    signal_types = {
        first_signal.signal_type,
        second_signal.signal_type,
    }

    # Two metric anomalies are directly comparable.
    if signal_types == {"metric_anomaly"}:
        return 1.0

    # Metric anomaly + error log is a strong relationship.
    if signal_types == {
        "metric_anomaly",
        "log_error",
    }:
        return 1.0

    # Metric anomaly + deployment is useful evidence.
    if signal_types == {
        "metric_anomaly",
        "deployment",
    }:
        return 1.0

    # Deployment + error log is also meaningful.
    if signal_types == {
        "deployment",
        "log_error",
    }:
        return 0.8

    return 0.0


# =========================================================
# DEPLOYMENT PROXIMITY
# =========================================================


def _calculate_deployment_score(
    first_signal: CorrelationSignal,
    second_signal: CorrelationSignal,
    temporal_score: float,
) -> tuple[float, bool]:
    """
    Give deployment-related signal pairs a deployment
    proximity score.

    The temporal score is reused because deployment
    proximity is specifically about how close the
    deployment occurred to the other signal.

    A deployment is only considered nearby when it falls
    inside the correlation window.
    """

    deployment_involved = (
        first_signal.signal_type == "deployment"
        or second_signal.signal_type == "deployment"
    )

    if not deployment_involved:
        return 0.0, False

    if temporal_score <= 0:
        return 0.0, False

    return temporal_score, True


# =========================================================
# CORRELATION LEVEL
# =========================================================


def _determine_correlation_level(
    score: float,
    config: CorrelationConfig,
) -> CorrelationLevel:

    if score < config.weak_threshold:
        return CorrelationLevel.NONE

    if score < config.moderate_threshold:
        return CorrelationLevel.WEAK

    if score < config.strong_threshold:
        return CorrelationLevel.MODERATE

    if score < config.very_strong_threshold:
        return CorrelationLevel.STRONG

    return CorrelationLevel.VERY_STRONG


# =========================================================
# CORRELATION ENGINE
# =========================================================


def correlate_signals(
    first_signal: CorrelationSignal,
    second_signal: CorrelationSignal,
    config: CorrelationConfig | None = None,
) -> CorrelationResult:

    if config is None:
        config = CorrelationConfig()

    _validate_config(config)

    # ---------------------------------------------------------
    # Calculate time difference
    # ---------------------------------------------------------

    time_difference = abs(
        (
            first_signal.timestamp
            - second_signal.timestamp
        ).total_seconds()
    )

    # ---------------------------------------------------------
    # Calculate individual scores
    # ---------------------------------------------------------

    temporal_score = _calculate_temporal_score(
        time_difference_seconds=time_difference,
        correlation_window_seconds=(
            config.correlation_window_seconds
        ),
    )

    service_score = _calculate_service_score(
        first_signal=first_signal,
        second_signal=second_signal,
    )

    telemetry_score = _calculate_telemetry_score(
        first_signal=first_signal,
        second_signal=second_signal,
    )

    deployment_score, deployment_nearby = (
        _calculate_deployment_score(
            first_signal=first_signal,
            second_signal=second_signal,
            temporal_score=temporal_score,
        )
    )

    # ---------------------------------------------------------
    # Calculate weighted correlation score
    # ---------------------------------------------------------

    correlation_score = (
        temporal_score * config.temporal_weight
        + service_score * config.service_weight
        + telemetry_score * config.telemetry_weight
        + deployment_score * config.deployment_weight
    )

    correlation_score = max(
        0.0,
        min(1.0, correlation_score),
    )

    # ---------------------------------------------------------
    # Determine correlation level
    # ---------------------------------------------------------

    correlation_level = _determine_correlation_level(
        score=correlation_score,
        config=config,
    )

    # ---------------------------------------------------------
    # Build explanation
    # ---------------------------------------------------------

    reasons: list[str] = []

    if temporal_score > 0:
        reasons.append(
            f"Signals occurred "
            f"{time_difference:.2f} seconds apart."
        )
    else:
        reasons.append(
            "Signals occurred outside the correlation window."
        )

    if service_score == 1.0:
        reasons.append(
            "Signals belong to the same service."
        )
    else:
        reasons.append(
            "Signals belong to different services."
        )

    if telemetry_score > 0:
        reasons.append(
            "Signal types have a recognized telemetry relationship."
        )
    else:
        reasons.append(
            "No recognized telemetry relationship was found."
        )

    if deployment_nearby:
        reasons.append(
            "A deployment occurred within the correlation window."
        )

    return CorrelationResult(
        related_signal_id=second_signal.id,
        related_signal_type=second_signal.signal_type,
        related_signal_name=second_signal.name,
        correlation_score=correlation_score,
        correlation_level=correlation_level,
        temporal_score=temporal_score,
        service_score=service_score,
        telemetry_score=telemetry_score,
        deployment_score=deployment_score,
        time_difference_seconds=time_difference,
        same_service=service_score == 1.0,
        deployment_nearby=deployment_nearby,
        reasons=reasons,
    )