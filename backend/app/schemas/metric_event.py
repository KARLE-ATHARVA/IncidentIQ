from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MetricEventCreate(BaseModel):
    timestamp: datetime
    name: str = Field(min_length=1, max_length=255)
    value: float


class MetricEventResponse(BaseModel):
    id: UUID
    service_id: UUID
    timestamp: datetime
    name: str
    value: float

    model_config = {"from_attributes": True}