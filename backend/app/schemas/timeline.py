from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


TimelineEventType = Literal["metric", "log", "deployment"]


class TimelineEvent(BaseModel):
    id: UUID
    timestamp: datetime
    event_type: TimelineEventType
    service_id: UUID
    title: str
    description: str | None = None
    source_id: UUID
    severity: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    incident_id: UUID
    start_time: datetime
    end_time: datetime
    events: list[TimelineEvent]