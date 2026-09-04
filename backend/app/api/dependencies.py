from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.service import Service
from backend.app.models.user import User


def get_authorized_service(
    project_id: UUID,
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Service:
    service = (
        db.query(Service)
        .join(Service.project)
        .filter(
            Service.id == service_id,
            Service.project_id == project_id,
            Service.project.has(owner_id=current_user.id),
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    return service