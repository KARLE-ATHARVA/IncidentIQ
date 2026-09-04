from uuid import UUID

from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    project_id: UUID

    model_config = {
        "from_attributes": True,
    }
