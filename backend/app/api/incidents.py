from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.incident import (
    IncidentDetail,
    IncidentListResponse,
    IncidentSummary,
)
from backend.app.schemas.incident import (
    IncidentDetail,
    IncidentListResponse,
    IncidentStatusResponse,
    IncidentSummary,
)
from backend.app.services.incident_lifecycle import (
    resolve_incident,
    start_incident_investigation,
)

router = APIRouter(
    prefix="/api/projects/{project_id}/incidents",
    tags=["incidents"],
)


def get_authorized_project(
    project_id: UUID,
    db: Session,
    current_user: User,
) -> Project:
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


@router.get(
    "",
    response_model=IncidentListResponse,
)
def list_incidents(
    project_id: UUID,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    severity: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    query = (
        db.query(Incident)
        .filter(
            Incident.project_id == project_id
        )
    )

    if status_filter is not None:
        query = query.filter(
            Incident.status == status_filter
        )

    if severity is not None:
        query = query.filter(
            Incident.severity == severity
        )

    if start_time is not None:
        query = query.filter(
            Incident.detected_at >= start_time
        )

    if end_time is not None:
        query = query.filter(
            Incident.detected_at <= end_time
        )

    incidents = (
        query
        .order_by(Incident.detected_at.desc())
        .limit(limit)
        .all()
    )

    return IncidentListResponse(
        items=incidents,
        count=len(incidents),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentDetail,
)
def get_incident(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.project_id == project_id,
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    return incident

@router.post(
    "/{incident_id}/start-investigation",
    response_model=IncidentStatusResponse,
)
def start_investigation(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.project_id == project_id,
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    try:
        return start_incident_investigation(
            db=db,
            incident=incident,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentStatusResponse,
)
def resolve(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.project_id == project_id,
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    try:
        return resolve_incident(
            db=db,
            incident=incident,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )