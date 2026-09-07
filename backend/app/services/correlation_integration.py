from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.services.correlation import (
    CorrelationConfig,
    CorrelationResult,
    CorrelationSignal,
    correlate_signals,
)


def correlate_metric_event_with_telemetry(
    db: Session,
    metric_event_id: UUID,
    config: CorrelationConfig | None = None,
) -> list[CorrelationResult]:
    """
    Compare a metric event with nearby logs and deployments.

    Database access is intentionally kept outside the core
    correlation algorithm.
    """

    metric_event = db.get(MetricEvent, metric_event_id)

    if metric_event is None:
        raise ValueError(
            f"Metric event '{metric_event_id}' was not found."
        )

    correlation_config = config or CorrelationConfig()

    window_seconds = correlation_config.correlation_window_seconds

    start_time = datetime.fromtimestamp(
        metric_event.timestamp.timestamp() - window_seconds,
        tz=metric_event.timestamp.tzinfo,
    )

    end_time = datetime.fromtimestamp(
        metric_event.timestamp.timestamp() + window_seconds,
        tz=metric_event.timestamp.tzinfo,
    )

    metric_signal = CorrelationSignal(
        id=metric_event.id,
        service_id=metric_event.service_id,
        timestamp=metric_event.timestamp,
        signal_type="metric_anomaly",
        name=metric_event.name,
    )

    results: list[CorrelationResult] = []

    logs_query = (
        select(LogEvent)
        .where(
            LogEvent.service_id == metric_event.service_id,
            LogEvent.timestamp >= start_time,
            LogEvent.timestamp <= end_time,
        )
        .order_by(LogEvent.timestamp)
    )

    logs = db.scalars(logs_query).all()

    for log in logs:
        if log.level.lower() not in {"error", "critical"}:
            continue

        log_signal = CorrelationSignal(
            id=log.id,
            service_id=log.service_id,
            timestamp=log.timestamp,
            signal_type="log_error",
            name=log.message,
        )

        results.append(
            correlate_signals(
                metric_signal,
                log_signal,
                config=correlation_config,
            )
        )

    deployments_query = (
        select(DeploymentEvent)
        .where(
            DeploymentEvent.service_id == metric_event.service_id,
            DeploymentEvent.timestamp >= start_time,
            DeploymentEvent.timestamp <= end_time,
        )
        .order_by(DeploymentEvent.timestamp)
    )

    deployments = db.scalars(deployments_query).all()

    for deployment in deployments:
        deployment_signal = CorrelationSignal(
            id=deployment.id,
            service_id=deployment.service_id,
            timestamp=deployment.timestamp,
            signal_type="deployment",
            name=deployment.version,
        )

        results.append(
            correlate_signals(
                metric_signal,
                deployment_signal,
                config=correlation_config,
            )
        )

    return results