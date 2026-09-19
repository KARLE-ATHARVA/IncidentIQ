from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.models.service import Service
from backend.app.services.incident_formation import IncidentCandidate


def ensure_incident_evidence(
    db: Session,
    incident: Incident,
    timeline_events: list[dict],
) -> bool:
    existing_source_ids = {
        evidence.source_id
        for evidence in db.query(EvidenceItem).filter(
            EvidenceItem.incident_id == incident.id,
        ).all()
    }

    evidence_added = False

    for event in timeline_events:
        source_id = UUID(str(event["source_id"]))

        if source_id in existing_source_ids:
            continue

        db.add(
            EvidenceItem(
                incident_id=incident.id,
                source_type="telemetry",
                source_id=source_id,
                title=event["title"],
                description=event["description"],
                collected_at=datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                ),
            )
        )
        existing_source_ids.add(source_id)
        evidence_added = True

    if evidence_added:
        db.flush()

    return evidence_added


def persist_incident_candidate(
    db: Session,
    candidate: IncidentCandidate,
) -> Incident:
    """
    Persist an IncidentCandidate and its supporting evidence.

    This function handles database persistence only.
    It does not perform detection, correlation, or
    root-cause analysis.
    """

    service = db.get(Service, candidate.service_id)

    if service is None:
        raise ValueError(
            f"Service '{candidate.service_id}' was not found."
        )

    incident = Incident(
        project_id=service.project_id,
        title=candidate.title,
        description=candidate.description,
        severity=candidate.severity.value,
        status="open",
        detected_at=candidate.detected_at,
    )

    db.add(incident)
    db.flush()

    for signal_id in candidate.supporting_signal_ids:
        evidence = EvidenceItem(
            incident_id=incident.id,
            source_type="telemetry",
            source_id=signal_id,
            title="Supporting telemetry evidence",
            description=(
                "Telemetry signal supporting the incident "
                "candidate."
            ),
            collected_at=candidate.detected_at,
        )

        db.add(evidence)

    db.commit()
    db.refresh(incident)

    return incident