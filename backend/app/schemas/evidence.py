from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvidenceInspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    incident_id: UUID
    source_type: str
    source_id: UUID
    title: str
    description: str
    collected_at: datetime
    service_id: UUID | None
    timestamp: datetime | None
    details: dict[str, Any]