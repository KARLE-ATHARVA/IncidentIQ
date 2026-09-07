from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.investigation import InvestigationResponse
from backend.app.services.investigation_lifecycle import (
    complete_investigation,
    create_investigation,
    fail_investigation,
    start_investigation,
)


router = APIRouter(
    prefix="/api/projects/{project_id}/incidents/{incident_id}/investigations",
    tags=["investigations"],
)


def get_authorized_incident(
    project_id: UUID,
    incident_id: UUID,
    db: Session,
    current_user: User,
) -> Incident:
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

    return incident


def get_authorized_investigation(
    project_id: UUID,
    incident_id: UUID,
    investigation_id: UUID,
    db: Session,
    current_user: User,
) -> Investigation:
    get_authorized_incident(
        project_id=project_id,
        incident_id=incident_id,
        db=db,
        current_user=current_user,
    )

    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id == investigation_id,
            Investigation.incident_id == incident_id,
        )
        .first()
    )

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found.",
        )

    return investigation


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_investigation(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = get_authorized_incident(
        project_id=project_id,
        incident_id=incident_id,
        db=db,
        current_user=current_user,
    )

    investigation = create_investigation(
        db=db,
        incident_id=incident.id,
    )

    return investigation


@router.post(
    "/{investigation_id}/start",
    response_model=InvestigationResponse,
)
def start_existing_investigation(
    project_id: UUID,
    incident_id: UUID,
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigation = get_authorized_investigation(
        project_id=project_id,
        incident_id=incident_id,
        investigation_id=investigation_id,
        db=db,
        current_user=current_user,
    )

    try:
        return start_investigation(
            db=db,
            investigation=investigation,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{investigation_id}/complete",
    response_model=InvestigationResponse,
)
def complete_existing_investigation(
    project_id: UUID,
    incident_id: UUID,
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigation = get_authorized_investigation(
        project_id=project_id,
        incident_id=incident_id,
        investigation_id=investigation_id,
        db=db,
        current_user=current_user,
    )

    try:
        return complete_investigation(
            db=db,
            investigation=investigation,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{investigation_id}/fail",
    response_model=InvestigationResponse,
)
def fail_existing_investigation(
    project_id: UUID,
    incident_id: UUID,
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigation = get_authorized_investigation(
        project_id=project_id,
        incident_id=incident_id,
        investigation_id=investigation_id,
        db=db,
        current_user=current_user,
    )

    try:
        return fail_investigation(
            db=db,
            investigation=investigation,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
