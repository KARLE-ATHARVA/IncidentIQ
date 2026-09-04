from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_authorized_service
from backend.app.db.dependencies import get_db
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.service import Service
from backend.app.schemas import (
    DeploymentEventCreate,
    DeploymentEventResponse,
    LogEventCreate,
    LogEventResponse,
    MetricEventCreate,
    MetricEventResponse,
)
from backend.app.services.telemetry import (
    create_deployment_event,
    create_log_event,
    create_metric_event,
)


router = APIRouter(
    prefix="/api/projects/{project_id}/services/{service_id}",
    tags=["telemetry"],
)


# =========================================================
# LOGS
# =========================================================

@router.post(
    "/logs",
    response_model=LogEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    project_id: UUID,
    service_id: UUID,
    data: LogEventCreate,
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    return create_log_event(
        db=db,
        service_id=service.id,
        data=data,
    )


@router.get(
    "/logs",
    response_model=list[LogEventResponse],
)
def get_logs(
    project_id: UUID,
    service_id: UUID,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    query = (
        db.query(LogEvent)
        .filter(LogEvent.service_id == service.id)
    )

    if start_time is not None:
        query = query.filter(
            LogEvent.timestamp >= start_time
        )

    if end_time is not None:
        query = query.filter(
            LogEvent.timestamp <= end_time
        )

    return (
        query
        .order_by(LogEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


# =========================================================
# METRICS
# =========================================================

@router.post(
    "/metrics",
    response_model=MetricEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
    project_id: UUID,
    service_id: UUID,
    data: MetricEventCreate,
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    return create_metric_event(
        db=db,
        service_id=service.id,
        data=data,
    )


@router.get(
    "/metrics",
    response_model=list[MetricEventResponse],
)
def get_metrics(
    project_id: UUID,
    service_id: UUID,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    query = (
        db.query(MetricEvent)
        .filter(MetricEvent.service_id == service.id)
    )

    if start_time is not None:
        query = query.filter(
            MetricEvent.timestamp >= start_time
        )

    if end_time is not None:
        query = query.filter(
            MetricEvent.timestamp <= end_time
        )

    return (
        query
        .order_by(MetricEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


# =========================================================
# DEPLOYMENTS
# =========================================================

@router.post(
    "/deployments",
    response_model=DeploymentEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deployment(
    project_id: UUID,
    service_id: UUID,
    data: DeploymentEventCreate,
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    return create_deployment_event(
        db=db,
        service_id=service.id,
        data=data,
    )


@router.get(
    "/deployments",
    response_model=list[DeploymentEventResponse],
)
def get_deployments(
    project_id: UUID,
    service_id: UUID,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    service: Service = Depends(get_authorized_service),
):
    query = (
        db.query(DeploymentEvent)
        .filter(DeploymentEvent.service_id == service.id)
    )

    if start_time is not None:
        query = query.filter(
            DeploymentEvent.timestamp >= start_time
        )

    if end_time is not None:
        query = query.filter(
            DeploymentEvent.timestamp <= end_time
        )

    return (
        query
        .order_by(DeploymentEvent.timestamp.desc())
        .limit(limit)
        .all()
    )