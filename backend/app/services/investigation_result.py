from sqlalchemy.orm import Session

from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.investigation_result_evidence import (
    InvestigationResultEvidence,
)
from backend.app.services.investigation_context import (
    InvestigationResultContext,
    validate_investigation_hypothesis,
)


def persist_investigation_result(
    db: Session,
    investigation: Investigation,
    result_context: InvestigationResultContext,
) -> InvestigationResult:
    """
    Persist an evidence-backed investigation result.

    Every supporting evidence ID must belong to the same incident
    as the investigation. This prevents an investigation result from
    referencing evidence belonging to another incident.
    """

    validate_investigation_hypothesis(result_context.hypothesis)

    if investigation.incident_id is None:
        raise ValueError(
            "Investigation must belong to an incident."
        )

    supporting_evidence_ids = (
        result_context.hypothesis.supporting_evidence_ids
    )

    evidence_items = (
        db.query(EvidenceItem)
        .filter(
            EvidenceItem.id.in_(supporting_evidence_ids),
            EvidenceItem.incident_id == investigation.incident_id,
        )
        .all()
    )

    found_evidence_ids = {
        evidence.id
        for evidence in evidence_items
    }

    missing_evidence_ids = (
        set(supporting_evidence_ids) - found_evidence_ids
    )

    if missing_evidence_ids:
        raise ValueError(
            "One or more supporting evidence items do not belong "
            "to the investigation incident."
        )

    alternative_explanations = "\n".join(
        f"- {explanation}"
        for explanation in (
            result_context.hypothesis.alternative_explanations
        )
    )

    next_steps = "\n".join(
        f"- {step}"
        for step in result_context.hypothesis.next_steps
    )

    investigation_result = InvestigationResult(
        investigation_id=investigation.id,
        hypothesis=result_context.hypothesis.hypothesis.strip(),
        confidence=result_context.hypothesis.confidence,
        reasoning=result_context.hypothesis.reasoning.strip(),
        alternative_explanations=(
            alternative_explanations or None
        ),
        next_steps=next_steps or None,
    )

    db.add(investigation_result)
    db.flush()

    for evidence_id in supporting_evidence_ids:
        db.add(
            InvestigationResultEvidence(
                investigation_result_id=investigation_result.id,
                evidence_item_id=evidence_id,
            )
        )

    db.commit()
    db.refresh(investigation_result)

    return investigation_result