from uuid import UUID

from pydantic import BaseModel, Field


class AIInvestigationOutput(BaseModel):
    """
    Structured output expected from an AI investigation reasoner.

    This schema represents untrusted model output before it is
    converted into IncidentIQ's internal investigation result.
    """

    hypothesis: str = Field(
        min_length=1,
        description="A possible explanation for the incident.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model-estimated confidence in the hypothesis.",
    )

    reasoning: str = Field(
        min_length=1,
        description="Evidence-based reasoning supporting the hypothesis.",
    )

    supporting_evidence_ids: list[UUID] = Field(
        min_length=1,
        description="Evidence item IDs supporting the hypothesis.",
    )

    alternative_explanations: list[str] = Field(
        min_length=1,
        description="Plausible alternative explanations.",
    )

    next_steps: list[str] = Field(
        min_length=1,
        description="Recommended investigation steps.",
    )
