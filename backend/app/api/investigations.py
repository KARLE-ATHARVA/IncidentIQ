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
from backend.app.schemas.investigation_result import (
    InvestigationResultEvidenceResponse,
    InvestigationResultResponse,
)
from backend.app.services.ai_reasoner import AIReasoner
from backend.app.services.incident_persistence import (
    ensure_incident_evidence,
)
from backend.app.services.investigation_context import (
    build_investigation_context,
)
from backend.app.services.investigation_evaluation import (
    evaluate_investigation_result,
)
from backend.app.services.investigation_lifecycle import (
    complete_investigation,
    create_investigation,
    fail_investigation,
    start_investigation,
)
from backend.app.services.investigation_reasoning import (
    DeterministicReasoner,
)
from backend.app.services.investigation_result import (
    persist_investigation_result,
)
from backend.app.services.investigation_result_retrieval import (
    get_investigation_result,
    get_result_evidence,
)
from backend.app.services.reasoning_engine import ReasoningEngine


router = APIRouter(
    prefix="/api/projects/{project_id}/incidents/{incident_id}/investigations",
    tags=["investigations"],
)


# ---------------------------------------------------------------------------
# Reasoning engine dependency
# ---------------------------------------------------------------------------


def get_reasoning_engine() -> ReasoningEngine:
    """
    Return the reasoning engine used for investigation generation.

    AIReasoner is the primary production reasoning implementation.
    DeterministicReasoner remains available as the fallback implementation.
    """
    return AIReasoner()


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Investigation lifecycle
# ---------------------------------------------------------------------------


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
        ) from exc


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
        ) from exc


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
        ) from exc


# ---------------------------------------------------------------------------
# Investigation retrieval
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# AI investigation result generation
# ---------------------------------------------------------------------------


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
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine),
):
    investigation = get_authorized_investigation(
        project_id=project_id,
        incident_id=incident_id,
        investigation_id=investigation_id,
        db=db,
        current_user=current_user,
    )

    if investigation.status == "pending":
        investigation = start_investigation(
            db=db,
            investigation=investigation,
        )

    try:
        # ---------------------------------------------------------------
        # 1. Build investigation context
        # ---------------------------------------------------------------

        context = build_investigation_context(
            db=db,
            incident=investigation.incident,
        )

        # ---------------------------------------------------------------
        # 2. Ensure evidence exists before reasoning
        # ---------------------------------------------------------------

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

        # ---------------------------------------------------------------
        # 3. Generate investigation result
        # ---------------------------------------------------------------

        reasoning_source = "ai"

        try:
            result_context = reasoning_engine.generate(
                context=context,
            )

        except (RuntimeError, ValueError):
            # AI reasoning failed.
            # Use deterministic reasoning as a safe fallback.
            reasoning_source = "deterministic_fallback"

            result_context = DeterministicReasoner().generate(
                context=context,
            )

        # ---------------------------------------------------------------
        # 4. Evaluate generated investigation result
        # ---------------------------------------------------------------

        evaluation = evaluate_investigation_result(
            context=context,
            hypothesis=result_context.hypothesis,
            reasoning_source=reasoning_source,
        )

        # ---------------------------------------------------------------
        # 5. Reject invalid investigation results
        # ---------------------------------------------------------------

        if not evaluation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Investigation result failed validation.",
                    "errors": evaluation.errors,
                    "warnings": evaluation.warnings,
                    "evidence_count": evaluation.evidence_count,
                    "supporting_evidence_count": (
                        evaluation.supporting_evidence_count
                    ),
                    "evidence_coverage": evaluation.evidence_coverage,
                },
            )

        # ---------------------------------------------------------------
        # 6. Persist validated result
        # ---------------------------------------------------------------

        result = persist_investigation_result(
            db=db,
            investigation=investigation,
            result_context=result_context,
            reasoning_source=reasoning_source,
        )

        # ---------------------------------------------------------------
        # 7. Mark investigation as completed
        # ---------------------------------------------------------------

        complete_investigation(
            db=db,
            investigation=investigation,
        )

        # ---------------------------------------------------------------
        # 8. Load persisted evidence links
        # ---------------------------------------------------------------

        evidence_items = get_result_evidence(
            db=db,
            result_id=result.id,
        )

        # ---------------------------------------------------------------
        # 9. Return result + evaluation metadata
        # ---------------------------------------------------------------

        return {
            "id": str(result.id),
            "investigation_id": str(result.investigation_id),
            "reasoning_source": result.reasoning_source,
            "hypothesis": result.hypothesis,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "alternative_explanations": [
                line.removeprefix("- ").strip()
                for line in (
                    result.alternative_explanations or ""
                ).splitlines()
                if line.strip()
            ],
            "next_steps": [
                line.removeprefix("- ").strip()
                for line in (
                    result.next_steps or ""
                ).splitlines()
                if line.strip()
            ],
            "supporting_evidence": [
                {
                    "id": str(evidence.id),
                    "evidence_id": str(evidence.id),
                    "source_type": evidence.source_type,
                    "source_id": str(evidence.source_id),
                    "title": evidence.title,
                    "description": evidence.description,
                    "collected_at": evidence.collected_at,
                }
                for evidence in evidence_items
            ],
            "evaluation": {
                "is_valid": evaluation.is_valid,
                "warnings": evaluation.warnings,
                "evidence_count": evaluation.evidence_count,
                "supporting_evidence_count": (
                    evaluation.supporting_evidence_count
                ),
                "evidence_coverage": evaluation.evidence_coverage,
            },
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Investigation result retrieval
# ---------------------------------------------------------------------------


@router.get(
    "/{investigation_id}/result",
    response_model=dict,
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

    return {
        "id": str(result.id),
        "investigation_id": str(result.investigation_id),
        "created_at": result.created_at,
        "reasoning_source": result.reasoning_source,
        "hypothesis": result.hypothesis,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "alternative_explanations": [
            line.removeprefix("- ").strip()
            for line in (
                result.alternative_explanations or ""
            ).splitlines()
            if line.strip()
        ],
        "next_steps": [
            line.removeprefix("- ").strip()
            for line in (
                result.next_steps or ""
            ).splitlines()
            if line.strip()
        ],
        "supporting_evidence": [
            {
                "id": str(evidence.id),
                "evidence_id": str(evidence.id),
                "source_type": evidence.source_type,
                "source_id": str(evidence.source_id),
                "title": evidence.title,
                "description": evidence.description,
                "collected_at": evidence.collected_at,
            }
            for evidence in evidence_items
        ],
    }