from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.services.correlation import (
    CorrelationLevel,
    CorrelationResult,
)
from backend.app.services.incident_formation import (
    IncidentCandidateSeverity,
    form_incident_candidate,
)


def make_result(
    *,
    score: float,
    level: CorrelationLevel,
    signal_type: str = "log_error",
    signal_id=None,
):
    return CorrelationResult(
        related_signal_id=signal_id or uuid4(),
        related_signal_type=signal_type,
        related_signal_name="test-signal",
        correlation_score=score,
        correlation_level=level,
        temporal_score=0.9,
        service_score=1.0,
        telemetry_score=1.0,
        deployment_score=0.0,
        time_difference_seconds=30.0,
        same_service=True,
        deployment_nearby=False,
        reasons=[
            "Signals occurred 30 seconds apart.",
            "Signals belong to the same service.",
        ],
    )


def test_no_correlations_produces_no_incident():
    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[],
    )

    assert candidate is None


def test_only_weak_correlations_produce_no_incident():
    result = make_result(
        score=0.40,
        level=CorrelationLevel.WEAK,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[result],
    )

    assert candidate is None


def test_moderate_correlation_creates_medium_incident():
    result = make_result(
        score=0.55,
        level=CorrelationLevel.MODERATE,
    )

    metric_event_id = uuid4()

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=metric_event_id,
        correlation_results=[result],
    )

    assert candidate is not None
    assert candidate.severity == IncidentCandidateSeverity.MEDIUM
    assert candidate.correlation_count == 1
    assert candidate.strongest_correlation_score == 0.55


def test_strong_correlation_creates_high_incident():
    result = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[result],
    )

    assert candidate is not None
    assert candidate.severity == IncidentCandidateSeverity.HIGH


def test_very_strong_correlation_creates_critical_incident():
    result = make_result(
        score=0.90,
        level=CorrelationLevel.VERY_STRONG,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[result],
    )

    assert candidate is not None
    assert candidate.severity == IncidentCandidateSeverity.CRITICAL


def test_multiple_correlations_preserve_supporting_evidence():
    metric_event_id = uuid4()
    log_event_id = uuid4()
    deployment_event_id = uuid4()

    log_result = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
        signal_type="log_error",
        signal_id=log_event_id,
    )

    deployment_result = make_result(
        score=0.80,
        level=CorrelationLevel.STRONG,
        signal_type="deployment",
        signal_id=deployment_event_id,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=metric_event_id,
        correlation_results=[
            log_result,
            deployment_result,
        ],
    )

    assert candidate is not None

    assert candidate.correlation_count == 2

    assert metric_event_id in candidate.supporting_signal_ids
    assert log_event_id in candidate.supporting_signal_ids
    assert deployment_event_id in candidate.supporting_signal_ids

    assert len(candidate.supporting_signal_ids) == 3


def test_duplicate_supporting_signal_ids_are_removed():
    metric_event_id = uuid4()
    shared_signal_id = uuid4()

    result_one = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
        signal_id=shared_signal_id,
    )

    result_two = make_result(
        score=0.80,
        level=CorrelationLevel.STRONG,
        signal_id=shared_signal_id,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=metric_event_id,
        correlation_results=[
            result_one,
            result_two,
        ],
    )

    assert candidate is not None

    assert candidate.supporting_signal_ids.count(
        shared_signal_id
    ) == 1


def test_strongest_correlation_determines_severity():
    moderate_result = make_result(
        score=0.55,
        level=CorrelationLevel.MODERATE,
    )

    strong_result = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[
            moderate_result,
            strong_result,
        ],
    )

    assert candidate is not None

    assert candidate.severity == IncidentCandidateSeverity.HIGH
    assert candidate.strongest_correlation_score == 0.75


def test_candidate_contains_evidence_before_root_cause_language():
    result = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[result],
    )

    assert candidate is not None

    assert "incident candidate" in candidate.description.lower()
    assert "not a confirmed root cause" in (
        candidate.description.lower()
    )

    assert any(
        "metric anomaly" in reason.lower()
        for reason in candidate.reasons
    )


def test_supporting_signal_types_are_recorded():
    log_result = make_result(
        score=0.75,
        level=CorrelationLevel.STRONG,
        signal_type="log_error",
    )

    deployment_result = make_result(
        score=0.80,
        level=CorrelationLevel.STRONG,
        signal_type="deployment",
    )

    candidate = form_incident_candidate(
        service_id=uuid4(),
        metric_name="checkout_latency",
        metric_value=250.0,
        detected_at=datetime.now(),
        metric_event_id=uuid4(),
        correlation_results=[
            log_result,
            deployment_result,
        ],
    )

    assert candidate is not None

    reasons_text = " ".join(candidate.reasons)

    assert "log_error" in reasons_text
    assert "deployment" in reasons_text