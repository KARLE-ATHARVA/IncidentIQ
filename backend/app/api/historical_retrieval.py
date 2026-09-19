from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.historical_retrieval import (
    SimilarHistoricalIncidentResponse,
)
from backend.app.services.historical_retrieval import (
    DEFAULT_SIMILARITY_THRESHOLD,
)
from backend.app.services.incident_retrieval import retrieve_historical_context


router = APIRouter(
    prefix="/api/projects/{project_id}/incidents",
    tags=["historical-retrieval"],
)


@router.get(
    "/{incident_id}/similar-incidents",
    response_model=list[SimilarHistoricalIncidentResponse],
)
def get_similar_historical_incidents(
    project_id: UUID,
    incident_id: UUID,
    top_k: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    similarity_threshold: float = Query(
        default=DEFAULT_SIMILARITY_THRESHOLD,
        ge=0.0,
        le=1.0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SimilarHistoricalIncidentResponse]:
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
            status_code=404,
            detail="Incident not found.",
        )

    try:
        results = retrieve_historical_context(
            db=db,
            incident=incident,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return [
        SimilarHistoricalIncidentResponse(
            historical_incident_id=result.historical_incident_id,
            title=result.title,
            summary=result.summary,
            symptoms=result.symptoms,
            root_cause=result.root_cause,
            resolution=result.resolution,
            severity=result.severity,
            service_id=result.service_id,
            occurred_at=result.occurred_at,
            similarity_score=result.similarity_score,
        )
        for result in results
    ]