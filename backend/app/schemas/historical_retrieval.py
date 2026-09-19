from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SimilarHistoricalIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    historical_incident_id: UUID
    title: str
    summary: str
    symptoms: str
    root_cause: str | None
    resolution: str | None
    severity: str
    service_id: UUID | None
    occurred_at: datetime
    similarity_score: float