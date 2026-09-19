from sqlalchemy.orm import Session

from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.investigation_result_evidence import (
    InvestigationResultEvidence,
)


def get_investigation_result(
    db: Session,
    investigation_id,
) -> InvestigationResult | None:
    """
    Retrieve the most recently created investigation result
    for an investigation.
    """

    return (
        db.query(InvestigationResult)
        .filter(
            InvestigationResult.investigation_id == investigation_id,
        )
        .order_by(InvestigationResult.created_at.desc())
        .first()
    )


def get_result_evidence(
    db: Session,
    result_id,
) -> list[EvidenceItem]:
    """
    Retrieve evidence linked to an investigation result.
    """

    return (
        db.query(EvidenceItem)
        .join(
            InvestigationResultEvidence,
            InvestigationResultEvidence.evidence_item_id
            == EvidenceItem.id,
        )
        .filter(
            InvestigationResultEvidence.investigation_result_id
            == result_id,
        )
        .order_by(EvidenceItem.collected_at.asc())
        .all()
    )