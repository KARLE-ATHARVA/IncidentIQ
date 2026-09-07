from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.incident import Incident
from backend.app.models.metric_event import MetricEvent
from backend.app.services.correlation import CorrelationConfig
from backend.app.services.correlation_integration import (
    correlate_metric_event_with_telemetry,
)
from backend.app.services.detection import (
    AnomalyDetectionResult,
    DetectionConfig,
)
from backend.app.services.detection_integration import (
    detect_metric_event_anomaly,
)
from backend.app.services.incident_formation import (
    IncidentCandidate,
    form_incident_candidate,
)
from backend.app.services.incident_persistence import (
    persist_incident_candidate,
)


def process_metric_event_for_incident(
    db: Session,
    metric_event_id: UUID,
) -> Incident | None:
    """
    Run the initial IncidentIQ incident pipeline for
    a metric event.

    Pipeline:

        MetricEvent
            ↓
        Detection
            ↓
        Correlation
            ↓
        Incident Formation
            ↓
        Persistence

    A normal metric does not create an incident.
    """

    metric_event = db.get(
        MetricEvent,
        metric_event_id,
    )

    if metric_event is None:
        raise ValueError(
            f"Metric event '{metric_event_id}' was not found."
        )

    # ---------------------------------------------------------
    # 1. Detection
    # ---------------------------------------------------------

    detection_result: AnomalyDetectionResult = (
        detect_metric_event_anomaly(
            db=db,
            metric_event_id=metric_event.id,
            config=DetectionConfig(
                minimum_observations=10,
                persistence_window=3,
            ),
        )
    )

    if detection_result.status.value != "anomaly":
        return None

    # ---------------------------------------------------------
    # 2. Correlation
    # ---------------------------------------------------------

    correlation_results = (
        correlate_metric_event_with_telemetry(
            db=db,
            metric_event_id=metric_event.id,
            config=CorrelationConfig(),
        )
    )

    # ---------------------------------------------------------
    # 3. Incident formation
    # ---------------------------------------------------------

    candidate: IncidentCandidate | None = (
        form_incident_candidate(
            service_id=metric_event.service_id,
            metric_name=metric_event.name,
            metric_value=metric_event.value,
            detected_at=detection_result.detected_at,
            metric_event_id=metric_event.id,
            correlation_results=correlation_results,
        )
    )

    if candidate is None:
        return None

    # ---------------------------------------------------------
    # 4. Persistence
    # ---------------------------------------------------------

    return persist_incident_candidate(
        db=db,
        candidate=candidate,
    )