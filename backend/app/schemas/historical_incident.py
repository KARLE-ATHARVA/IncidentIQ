from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistoricalIncidentBase(BaseModel):
    title: str
    summary: str
    symptoms: str
    root_cause: str | None = None
    resolution: str | None = None


class HistoricalIncidentCreate(HistoricalIncidentBase):
    service_id: UUID | None = None


class HistoricalIncidentResponse(HistoricalIncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    project_id: UUID
    service_id: UUID | None
    severity: str
    occurred_at: datetime
    resolved_at: datetime | None
    created_at: datetime