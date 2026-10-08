from uuid import UUID

from pydantic import BaseModel


class SimulationResponse(BaseModel):
    scenario: str
    status: str
    incident_id: UUID | None = None
    severity: str | None = None
    incident_status: str | None = None
    title: str | None = None


class SimulationStateResponse(BaseModel):
    active: bool
    scenario: str | None = None
    status: str | None = None
    incident_id: UUID | None = None
    severity: str | None = None
    incident_status: str | None = None
    title: str | None = None


class SimulationResetResponse(BaseModel):
    status: str
    deleted_run_id: UUID | None = None