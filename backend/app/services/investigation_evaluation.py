from dataclasses import dataclass, field
from uuid import UUID

from backend.app.services.investigation_context import (
    InvestigationContext,
    InvestigationHypothesis,
    validate_investigation_hypothesis,
)


VALID_REASONING_SOURCES = {
    "ai",
    "deterministic_fallback",
}


@dataclass(frozen=True)
class InvestigationEvaluation:
    """
    Deterministic evaluation of an investigation result.

    This evaluates structural validity and evidence grounding.
    It does not determine whether the hypothesis is factually correct.
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_count: int = 0
    supporting_evidence_count: int = 0
    evidence_coverage: float = 0.0


def evaluate_investigation_result(
    context: InvestigationContext,
    hypothesis: InvestigationHypothesis,
    reasoning_source: str,
) -> InvestigationEvaluation:
    """
    Evaluate an investigation result against its supplied context.

    The evaluator checks:
    - structural hypothesis validity
    - evidence grounding
    - reasoning provenance
    - basic evidence sufficiency

    It does not decide whether the hypothesis is actually true.
    """

    errors: list[str] = []
    warnings: list[str] = []

    evidence_ids = {
        evidence.evidence_id
        for evidence in context.evidence_items
    }

    supporting_ids = set(hypothesis.supporting_evidence_ids)

    evidence_count = len(evidence_ids)
    supporting_evidence_count = len(supporting_ids)

    # ---------------------------------------------------------
    # Structural validation
    # ---------------------------------------------------------

    try:
        validate_investigation_hypothesis(hypothesis)
    except ValueError as exc:
        errors.append(str(exc))

    # ---------------------------------------------------------
    # Reasoning provenance
    # ---------------------------------------------------------

    if reasoning_source not in VALID_REASONING_SOURCES:
        errors.append(
            f"Unsupported reasoning source: {reasoning_source}."
        )

    # ---------------------------------------------------------
    # Evidence grounding
    # ---------------------------------------------------------

    missing_evidence_ids = supporting_ids - evidence_ids

    if missing_evidence_ids:
        errors.append(
            "One or more supporting evidence items are not present "
            "in the investigation context."
        )

    # ---------------------------------------------------------
    # Evidence coverage
    # ---------------------------------------------------------

    if evidence_count > 0:
        evidence_coverage = (
            len(supporting_ids & evidence_ids)
            / evidence_count
        )
    else:
        evidence_coverage = 0.0

    # ---------------------------------------------------------
    # Evidence sufficiency warnings
    # ---------------------------------------------------------

    if evidence_count == 0:
        errors.append(
            "Investigation context contains no evidence items."
        )

    elif supporting_evidence_count == 0:
        errors.append(
            "Investigation result does not reference supporting evidence."
        )

    elif supporting_evidence_count == 1:
        warnings.append(
            "Investigation is supported by only one evidence item."
        )

    if not context.timeline_events:
        warnings.append(
            "Investigation context contains no timeline events."
        )

    if not context.historical_incidents:
        warnings.append(
            "No historical incidents were available for contextual comparison."
        )

    # ---------------------------------------------------------
    # Final evaluation
    # ---------------------------------------------------------

    return InvestigationEvaluation(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        evidence_count=evidence_count,
        supporting_evidence_count=supporting_evidence_count,
        evidence_coverage=evidence_coverage,
    )