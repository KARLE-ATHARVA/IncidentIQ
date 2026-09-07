from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IncidentSummary(BaseModel):
    id: UUID
    title: str
    severity: str
    status: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    count: int


class IncidentDetail(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class IncidentStatusResponse(BaseModel):
    id: UUID
    status: str
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)