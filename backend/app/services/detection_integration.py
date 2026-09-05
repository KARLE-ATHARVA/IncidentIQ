from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.metric_event import MetricEvent
from backend.app.services.detection import (
    AnomalyDetectionResult,
    DetectionConfig,
    detect_anomaly,
)


def detect_metric_event_anomaly(
    db: Session,
    metric_event_id: UUID,
    config: DetectionConfig | None = None,
) -> AnomalyDetectionResult:
    """
    Load the required telemetry data from PostgreSQL and run
    the pure anomaly detection engine against it.

    Database access lives here rather than inside detection.py.
    """

    # ---------------------------------------------------------
    # 1. Load the current metric event
    # ---------------------------------------------------------

    current_event = db.get(MetricEvent, metric_event_id)

    if current_event is None:
        raise ValueError(
            f"Metric event '{metric_event_id}' was not found."
        )

    # ---------------------------------------------------------
    # 2. Load previous observations for the same metric
    # ---------------------------------------------------------

    previous_events_query = (
        select(MetricEvent)
        .where(
            MetricEvent.service_id == current_event.service_id,
            MetricEvent.name == current_event.name,
            MetricEvent.timestamp < current_event.timestamp,
        )
        .order_by(MetricEvent.timestamp.desc())
        .limit(25)
    )

    previous_events = list(
        reversed(
            db.scalars(previous_events_query).all()
        )
    )

    # ---------------------------------------------------------
    # 3. Separate historical and recent observations
    # ---------------------------------------------------------

    historical_count = 20
    recent_count = 5

    if len(previous_events) < historical_count + recent_count:
        historical_events = previous_events
        recent_events = []
    else:
        historical_events = previous_events[
            :historical_count
        ]

        recent_events = previous_events[
            historical_count:
        ]

        recent_events = recent_events[-recent_count:]

    historical_values = [
        event.value
        for event in historical_events
    ]

    recent_values = [
        event.value
        for event in recent_events
    ]

    # ---------------------------------------------------------
    # 4. Run the pure detection engine
    # ---------------------------------------------------------

    return detect_anomaly(
        metric_name=current_event.name,
        current_value=current_event.value,
        observed_at=current_event.timestamp,
        service_id=current_event.service_id,
        metric_event_id=current_event.id,
        historical_values=historical_values,
        recent_values=recent_values,
        config=config,
    )
