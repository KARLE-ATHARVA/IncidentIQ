from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.schemas.simulation import (
    SimulationResetResponse,
    SimulationResponse,
    SimulationStateResponse,
)
from backend.app.services.simulation import (
    get_simulation_state,
    reset_simulation,
    run_bad_deployment_simulation,
)


router = APIRouter(
    prefix="/api/projects/{project_id}/simulation",
    tags=["simulation"],
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
            status_code=404,
            detail="Project not found.",
        )

    return project


@router.get(
    "/state",
    response_model=SimulationStateResponse,
)
def simulation_state(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    simulation_run = get_simulation_state(
        db=db,
        project_id=project_id,
    )

    if simulation_run is None:
        return SimulationStateResponse(
            active=False,
        )

    incident = None

    if simulation_run.incident_id is not None:
        from backend.app.models.incident import Incident

        incident = db.get(
            Incident,
            simulation_run.incident_id,
        )

    return SimulationStateResponse(
        active=True,
        scenario=simulation_run.scenario,
        status=simulation_run.status,
        incident_id=(
            incident.id
            if incident is not None
            else simulation_run.incident_id
        ),
        severity=(
            incident.severity
            if incident is not None
            else None
        ),
        incident_status=(
            incident.status
            if incident is not None
            else None
        ),
        title=(
            incident.title
            if incident is not None
            else None
        ),
    )


@router.post(
    "/bad-deployment",
    response_model=SimulationResponse,
)
def bad_deployment(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    service = (
        db.query(Service)
        .filter(
            Service.project_id == project.id,
        )
        .order_by(Service.name.asc())
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="No service is available for simulation.",
        )

    try:
        simulation_run, incident = run_bad_deployment_simulation(
            db=db,
            project_id=project_id,
            service_id=service.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if incident is None:
        return SimulationResponse(
            scenario=simulation_run.scenario,
            status=simulation_run.status,
            incident_id=None,
            severity=None,
            incident_status=None,
            title=None,
        )

    return SimulationResponse(
        scenario=simulation_run.scenario,
        status=simulation_run.status,
        incident_id=incident.id,
        severity=incident.severity,
        incident_status=incident.status,
        title=incident.title,
    )


@router.post(
    "/reset",
    response_model=SimulationResetResponse,
)
def reset(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    simulation_run = reset_simulation(
        db=db,
        project_id=project_id,
    )

    if simulation_run is None:
        return SimulationResetResponse(
            status="no_active_simulation",
            deleted_run_id=None,
        )

    return SimulationResetResponse(
        status="reset",
        deleted_run_id=simulation_run.id,
    )
