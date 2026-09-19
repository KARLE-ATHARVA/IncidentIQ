from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InvestigationResultEvidenceResponse(BaseModel):
    id: UUID
    source_type: str
    source_id: UUID
    title: str
    description: str
    collected_at: datetime


class InvestigationResultResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    created_at: datetime
    hypothesis: str
    confidence: float
    reasoning: str
    alternative_explanations: list[str]
    next_steps: list[str]
    supporting_evidence: list[InvestigationResultEvidenceResponse]