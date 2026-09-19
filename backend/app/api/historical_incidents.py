from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.schemas.historical_incident import (
    HistoricalIncidentCreate,
    HistoricalIncidentResponse,
)
from backend.app.services.historical_incident import (
    create_historical_incident,
)

router = APIRouter(
    prefix="/api/projects/{project_id}",
    tags=["historical-incidents"],
)


def get_owned_project(
    db: Session,
    project_id: UUID,
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


@router.post(
    "/incidents/{incident_id}/historical-record",
    response_model=HistoricalIncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_historical_record(
    project_id: UUID,
    incident_id: UUID,
    payload: HistoricalIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoricalIncidentResponse:
    project = get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.project_id == project.id,
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    try:
        historical_incident = create_historical_incident(
            db=db,
            incident=incident,
            title=payload.title,
            summary=payload.summary,
            symptoms=payload.symptoms,
            root_cause=payload.root_cause,
            resolution=payload.resolution,
            service_id=payload.service_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return historical_incident


@router.get(
    "/historical-incidents",
    response_model=list[HistoricalIncidentResponse],
)
def list_historical_incidents(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HistoricalIncident]:
    project = get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    return (
        db.query(HistoricalIncident)
        .filter(
            HistoricalIncident.project_id == project.id,
        )
        .order_by(
            HistoricalIncident.occurred_at.desc(),
        )
        .all()
    )


@router.get(
    "/historical-incidents/{historical_incident_id}",
    response_model=HistoricalIncidentResponse,
)
def get_historical_incident(
    project_id: UUID,
    historical_incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoricalIncident:
    project = get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    historical_incident = (
        db.query(HistoricalIncident)
        .filter(
            HistoricalIncident.id == historical_incident_id,
            HistoricalIncident.project_id == project.id,
        )
        .first()
    )

    if historical_incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Historical incident not found.",
        )

    return historical_incident