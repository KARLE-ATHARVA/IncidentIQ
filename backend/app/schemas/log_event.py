from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogEventCreate(BaseModel):
    timestamp: datetime
    level: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1)


class LogEventResponse(BaseModel):
    id: UUID
    service_id: UUID
    timestamp: datetime
    level: str
    message: str

    model_config = {"from_attributes": True}