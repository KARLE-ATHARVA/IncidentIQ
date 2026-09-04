from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.schemas.deployment_event import DeploymentEventCreate
from backend.app.schemas.log_event import LogEventCreate
from backend.app.schemas.metric_event import MetricEventCreate


def create_log_event(
    db: Session,
    service_id: UUID,
    data: LogEventCreate,
) -> LogEvent:
    event = LogEvent(
        service_id=service_id,
        timestamp=data.timestamp,
        level=data.level,
        message=data.message,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def create_metric_event(
    db: Session,
    service_id: UUID,
    data: MetricEventCreate,
) -> MetricEvent:
    event = MetricEvent(
        service_id=service_id,
        timestamp=data.timestamp,
        name=data.name,
        value=data.value,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def create_deployment_event(
    db: Session,
    service_id: UUID,
    data: DeploymentEventCreate,
) -> DeploymentEvent:
    event = DeploymentEvent(
        service_id=service_id,
        timestamp=data.timestamp,
        version=data.version,
        description=data.description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event