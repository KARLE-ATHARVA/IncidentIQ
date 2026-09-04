from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID

    model_config = {
        "from_attributes": True,
    }