from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.incident import Incident
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.service import Service
from backend.app.schemas.timeline import TimelineEvent


@dataclass(frozen=True)
class TimelineConfig:
    window_minutes: int = 10

    def __post_init__(self) -> None:
        if self.window_minutes <= 0:
            raise ValueError("window_minutes must be greater than 0")


def calculate_timeline_window(
    detected_at: datetime,
    config: TimelineConfig | None = None,
) -> tuple[datetime, datetime]:
    config = config or TimelineConfig()

    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=timezone.utc)

    window = timedelta(minutes=config.window_minutes)
    return detected_at - window, detected_at + window


def normalize_metric_event(event: MetricEvent) -> TimelineEvent:
    return TimelineEvent(
        id=event.id,
        timestamp=event.timestamp,
        event_type="metric",
        service_id=event.service_id,
        title=event.name,
        description=f"{event.name} = {event.value}",
        source_id=event.id,
        severity=None,
        metadata={"metric_name": event.name, "value": event.value},
    )


def normalize_log_event(event: LogEvent) -> TimelineEvent:
    return TimelineEvent(
        id=event.id,
        timestamp=event.timestamp,
        event_type="log",
        service_id=event.service_id,
        title=f"{event.level} log",
        description=event.message,
        source_id=event.id,
        severity=event.level,
        metadata={"level": event.level, "message": event.message},
    )


def normalize_deployment_event(event: DeploymentEvent) -> TimelineEvent:
    return TimelineEvent(
        id=event.id,
        timestamp=event.timestamp,
        event_type="deployment",
        service_id=event.service_id,
        title=f"Deployment {event.version}",
        description=event.description,
        source_id=event.id,
        severity=None,
        metadata={
            "version": event.version,
            "deployment_description": event.description,
        },
    )


def build_timeline_events(
    metrics: list[MetricEvent],
    logs: list[LogEvent],
    deployments: list[DeploymentEvent],
) -> list[TimelineEvent]:
    events = [
        normalize_metric_event(event) for event in metrics
    ]
    events.extend(normalize_log_event(event) for event in logs)
    events.extend(normalize_deployment_event(event) for event in deployments)
    events.sort(key=lambda event: event.timestamp)
    return events


def reconstruct_incident_timeline(
    db: Session,
    incident: Incident,
    config: TimelineConfig | None = None,
) -> tuple[datetime, datetime, list[TimelineEvent]]:
    config = config or TimelineConfig()
    start_time, end_time = calculate_timeline_window(
        incident.detected_at,
        config,
    )

    metrics = db.scalars(
        select(MetricEvent)
        .join(Service, MetricEvent.service_id == Service.id)
        .where(
            Service.project_id == incident.project_id,
            MetricEvent.timestamp >= start_time,
            MetricEvent.timestamp <= end_time,
        )
        .order_by(MetricEvent.timestamp.asc())
    ).all()

    logs = db.scalars(
        select(LogEvent)
        .join(Service, LogEvent.service_id == Service.id)
        .where(
            Service.project_id == incident.project_id,
            LogEvent.timestamp >= start_time,
            LogEvent.timestamp <= end_time,
        )
        .order_by(LogEvent.timestamp.asc())
    ).all()

    deployments = db.scalars(
        select(DeploymentEvent)
        .join(Service, DeploymentEvent.service_id == Service.id)
        .where(
            Service.project_id == incident.project_id,
            DeploymentEvent.timestamp >= start_time,
            DeploymentEvent.timestamp <= end_time,
        )
        .order_by(DeploymentEvent.timestamp.asc())
    ).all()

    return (
        start_time,
        end_time,
        build_timeline_events(metrics, logs, deployments),
    )
