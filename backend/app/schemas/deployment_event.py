from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeploymentEventCreate(BaseModel):
    timestamp: datetime
    version: str = Field(min_length=1, max_length=255)
    description: str | None = None


class DeploymentEventResponse(BaseModel):
    id: UUID
    service_id: UUID
    timestamp: datetime
    version: str
    description: str | None

    model_config = {"from_attributes": True}