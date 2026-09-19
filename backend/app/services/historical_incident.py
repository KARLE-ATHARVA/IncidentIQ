from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.incident import Incident


def create_historical_incident(
    db: Session,
    incident: Incident,
    title: str,
    summary: str,
    symptoms: str,
    root_cause: str | None = None,
    resolution: str | None = None,
    service_id: UUID | None = None,
) -> HistoricalIncident:
    """
    Create a reusable historical knowledge record
    from a resolved incident.
    """

    if incident.status != "resolved":
        raise ValueError(
            "Only resolved incidents can be converted "
            "into historical incidents."
        )

    if incident.resolved_at is None:
        raise ValueError(
            "Resolved incident must have a resolved_at timestamp."
        )

    existing = (
        db.query(HistoricalIncident)
        .filter(
            HistoricalIncident.incident_id == incident.id
        )
        .first()
    )

    if existing is not None:
        raise ValueError(
            "A historical record already exists for this incident."
        )

    if not title.strip():
        raise ValueError("Historical incident title cannot be empty.")

    if not summary.strip():
        raise ValueError("Historical incident summary cannot be empty.")

    if not symptoms.strip():
        raise ValueError("Historical incident symptoms cannot be empty.")

    historical_incident = HistoricalIncident(
        incident_id=incident.id,
        project_id=incident.project_id,
        service_id=service_id,
        title=title.strip(),
        summary=summary.strip(),
        symptoms=symptoms.strip(),
        root_cause=root_cause.strip() if root_cause else None,
        resolution=resolution.strip() if resolution else None,
        severity=incident.severity,
        occurred_at=incident.detected_at,
        resolved_at=incident.resolved_at,
    )

    db.add(historical_incident)
    db.commit()
    db.refresh(historical_incident)

    return historical_incident