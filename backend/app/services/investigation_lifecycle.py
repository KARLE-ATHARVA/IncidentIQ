from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.investigation import Investigation


PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"


def create_investigation(
    db: Session,
    incident_id,
) -> Investigation:
    investigation = Investigation(
        incident_id=incident_id,
        status=PENDING,
    )

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation


def start_investigation(
    db: Session,
    investigation: Investigation,
) -> Investigation:
    if investigation.status != PENDING:
        raise ValueError(
            "Only pending investigations can be started."
        )

    investigation.status = RUNNING
    investigation.started_at = datetime.now(timezone.utc)

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation


def complete_investigation(
    db: Session,
    investigation: Investigation,
) -> Investigation:
    if investigation.status != RUNNING:
        raise ValueError(
            "Only running investigations can be completed."
        )

    investigation.status = COMPLETED
    investigation.completed_at = datetime.now(timezone.utc)

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation


def fail_investigation(
    db: Session,
    investigation: Investigation,
) -> Investigation:
    if investigation.status != RUNNING:
        raise ValueError(
            "Only running investigations can be failed."
        )

    investigation.status = FAILED
    investigation.completed_at = datetime.now(timezone.utc)

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation