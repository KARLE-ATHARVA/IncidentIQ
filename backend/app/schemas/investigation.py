from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvestigationResponse(BaseModel):
    id: UUID
    incident_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)