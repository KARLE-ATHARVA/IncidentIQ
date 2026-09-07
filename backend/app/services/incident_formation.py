from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from backend.app.services.correlation import (
    CorrelationLevel,
    CorrelationResult,
)


class IncidentCandidateSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class IncidentCandidate:
    service_id: UUID
    title: str
    description: str
    severity: IncidentCandidateSeverity

    detected_at: datetime

    primary_metric_name: str
    primary_metric_value: float

    correlation_count: int
    strongest_correlation_score: float

    supporting_signal_ids: list[UUID]

    reasons: list[str]


def _determine_severity(
    strongest_level: CorrelationLevel,
) -> IncidentCandidateSeverity:
    """
    Determine incident candidate severity from the
    strongest correlation level.

    Correlation strength is evidence of how strongly
    the signals are connected; it is not a root-cause claim.
    """

    if strongest_level == CorrelationLevel.VERY_STRONG:
        return IncidentCandidateSeverity.CRITICAL

    if strongest_level == CorrelationLevel.STRONG:
        return IncidentCandidateSeverity.HIGH

    return IncidentCandidateSeverity.MEDIUM


def form_incident_candidate(
    *,
    service_id: UUID,
    metric_name: str,
    metric_value: float,
    detected_at: datetime,
    metric_event_id: UUID,
    correlation_results: list[CorrelationResult],
) -> IncidentCandidate | None:
    """
    Convert sufficiently strong correlated evidence into
    an incident candidate.

    This function does not determine root cause.
    """

    # ---------------------------------------------------------
    # No correlated evidence
    # ---------------------------------------------------------

    if not correlation_results:
        return None

    # ---------------------------------------------------------
    # Keep only correlations strong enough to form
    # an incident candidate.
    # ---------------------------------------------------------

    qualifying_results = [
        result
        for result in correlation_results
        if result.correlation_score >= 0.50
    ]

    if not qualifying_results:
        return None

    # ---------------------------------------------------------
    # Find strongest supporting correlation
    # ---------------------------------------------------------

    strongest_result = max(
        qualifying_results,
        key=lambda result: result.correlation_score,
    )

    # ---------------------------------------------------------
    # Determine severity
    # ---------------------------------------------------------

    severity = _determine_severity(
        strongest_result.correlation_level
    )

    # ---------------------------------------------------------
    # Preserve evidence identity
    # ---------------------------------------------------------

    supporting_signal_ids = [metric_event_id]

    for result in qualifying_results:
        supporting_signal_ids.append(
            result.related_signal_id
        )

    # Remove duplicates while preserving order.
    supporting_signal_ids = list(
        dict.fromkeys(supporting_signal_ids)
    )

    # ---------------------------------------------------------
    # Build explanation
    # ---------------------------------------------------------

    reasons = [
        "Metric anomaly was detected.",
        (
            f"{len(qualifying_results)} correlated telemetry "
            "signal(s) met the incident threshold."
        ),
        (
            "Strongest correlation score: "
            f"{strongest_result.correlation_score:.3f}."
        ),
    ]

    # Include the types of supporting evidence.
    supporting_types = sorted(
        {
            result.related_signal_type
            for result in qualifying_results
        }
    )

    if supporting_types:
        reasons.append(
            "Supporting signal types: "
            + ", ".join(supporting_types)
            + "."
        )

    # ---------------------------------------------------------
    # Build candidate title
    # ---------------------------------------------------------

    title = (
        f"Potential incident: {metric_name} anomaly "
        f"on service {service_id}"
    )

    # ---------------------------------------------------------
    # Build candidate description
    # ---------------------------------------------------------

    description = (
        f"The metric '{metric_name}' reached "
        f"{metric_value} and was associated with "
        f"{len(qualifying_results)} correlated telemetry "
        "signal(s). This represents an incident candidate, "
        "not a confirmed root cause."
    )

    # ---------------------------------------------------------
    # Return domain object
    # ---------------------------------------------------------

    return IncidentCandidate(
        service_id=service_id,
        title=title,
        description=description,
        severity=severity,
        detected_at=detected_at,
        primary_metric_name=metric_name,
        primary_metric_value=metric_value,
        correlation_count=len(qualifying_results),
        strongest_correlation_score=(
            strongest_result.correlation_score
        ),
        supporting_signal_ids=supporting_signal_ids,
        reasons=reasons,
    )