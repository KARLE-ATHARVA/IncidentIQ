from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.timeline import TimelineResponse
from backend.app.services.timeline import reconstruct_incident_timeline


router = APIRouter(
    prefix="/api/projects/{project_id}/incidents/{incident_id}",
    tags=["timeline"],
)


@router.get(
    "/timeline",
    response_model=TimelineResponse,
)
def get_incident_timeline(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineResponse:
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

    start_time, end_time, events = reconstruct_incident_timeline(
        db=db,
        incident=incident,
    )

    return TimelineResponse(
        incident_id=incident.id,
        start_time=start_time,
        end_time=end_time,
        events=events,
    )