from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.incident import Incident


OPEN = "open"
INVESTIGATING = "investigating"
RESOLVED = "resolved"


def start_incident_investigation(
    db: Session,
    incident: Incident,
) -> Incident:
    """
    Transition an incident from OPEN to INVESTIGATING.

    Only an OPEN incident can start investigation.
    """

    if incident.status != OPEN:
        raise ValueError(
            "Only open incidents can be moved to investigating."
        )

    incident.status = INVESTIGATING

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def resolve_incident(
    db: Session,
    incident: Incident,
) -> Incident:
    """
    Resolve an incident.

    OPEN and INVESTIGATING incidents can be resolved.
    """

    if incident.status not in {
        OPEN,
        INVESTIGATING,
    }:
        raise ValueError(
            "Only open or investigating incidents can be resolved."
        )

    incident.status = RESOLVED
    incident.resolved_at = datetime.now(timezone.utc)

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident