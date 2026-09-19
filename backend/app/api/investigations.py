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
from backend.app.services.investigation_context import (
    build_investigation_context,
)
from backend.app.services.investigation_reasoning import (
    generate_deterministic_investigation,
)
from backend.app.services.investigation_result import (
    persist_investigation_result,
)
from backend.app.services.incident_persistence import (
    ensure_incident_evidence,
)
from backend.app.schemas.investigation_result import (
    InvestigationResultResponse,
    InvestigationResultEvidenceResponse,
)
from backend.app.services.investigation_result_retrieval import (
    get_investigation_result,
    get_result_evidence,
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

@router.get(
    "",
    response_model=list[InvestigationResponse],
)
def get_incident_investigations(
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

    investigations = (
        db.query(Investigation)
        .filter(
            Investigation.incident_id == incident.id,
        )
        .order_by(Investigation.started_at.desc())
        .all()
    )

    return investigations

@router.post(
    "/{investigation_id}/generate-result",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
def generate_investigation_result(
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
        context = build_investigation_context(
            db=db,
            incident=investigation.incident,
        )

        if not context.evidence_items:
            ensure_incident_evidence(
                db=db,
                incident=investigation.incident,
                timeline_events=context.timeline_events,
            )
            context = build_investigation_context(
                db=db,
                incident=investigation.incident,
            )

        result_context = generate_deterministic_investigation(
            context=context,
        )

        result = persist_investigation_result(
            db=db,
            investigation=investigation,
            result_context=result_context,
        )

        return {
            "id": str(result.id),
            "investigation_id": str(result.investigation_id),
            "hypothesis": result.hypothesis,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "next_steps": [
                line.removeprefix("- ").strip()
                for line in (result.next_steps or "").splitlines()
                if line.strip()
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

@router.get(
    "/{investigation_id}/result",
    response_model=InvestigationResultResponse,
)
def get_existing_investigation_result(
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

    result = get_investigation_result(
        db=db,
        investigation_id=investigation.id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation result not found.",
        )

    evidence_items = get_result_evidence(
        db=db,
        result_id=result.id,
    )

    alternative_explanations = []

    if result.alternative_explanations:
        alternative_explanations = [
            line.removeprefix("- ").strip()
            for line in result.alternative_explanations.splitlines()
            if line.strip()
        ]

    next_steps = []

    if result.next_steps:
        next_steps = [
            line.removeprefix("- ").strip()
            for line in result.next_steps.splitlines()
            if line.strip()
        ]

    return InvestigationResultResponse(
        id=result.id,
        investigation_id=result.investigation_id,
        created_at=result.created_at,
        hypothesis=result.hypothesis,
        confidence=result.confidence,
        reasoning=result.reasoning,
        alternative_explanations=alternative_explanations,
        next_steps=next_steps,
        supporting_evidence=[
            InvestigationResultEvidenceResponse(
                id=evidence.id,
                source_type=evidence.source_type,
                source_id=evidence.source_id,
                title=evidence.title,
                description=evidence.description,
                collected_at=evidence.collected_at,
            )
            for evidence in evidence_items
        ],
    )