from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.schemas.service import ServiceCreate, ServiceResponse


router = APIRouter(
    prefix="/api/projects/{project_id}/services",
    tags=["Services"],
)


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    project_id: UUID,
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    service = Service(
        name=service_data.name,
        project_id=project.id,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service

@router.get(
    "",
    response_model=list[ServiceResponse],
)
def list_services(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    services = db.scalars(
        select(Service)
        .where(Service.project_id == project.id)
        .order_by(Service.name)
    ).all()

    return services

@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
)
def get_service(
    project_id: UUID,
    service_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = db.scalar(
        select(Service)
        .join(Project, Service.project_id == Project.id)
        .where(
            Service.id == service_id,
            Service.project_id == project_id,
            Project.owner_id == current_user.id,
        )
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    return service