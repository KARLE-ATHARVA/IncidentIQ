from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.db.database import SessionLocal
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.services.incident_lifecycle import (
    INVESTIGATING,
    OPEN,
    RESOLVED,
    resolve_incident,
    start_incident_investigation,
)


def create_test_incident(status: str = OPEN):
    db = SessionLocal()

    user = User(
        email=f"lifecycle-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"Lifecycle Project {uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.flush()

    incident = Incident(
        project_id=project.id,
        title="Lifecycle test incident",
        description="Testing incident lifecycle.",
        severity="high",
        status=status,
        detected_at=datetime.now(timezone.utc),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return db, incident


def test_open_can_start_investigation():
    db, incident = create_test_incident(OPEN)

    try:
        updated = start_incident_investigation(
            db=db,
            incident=incident,
        )

        assert updated.status == INVESTIGATING
        assert updated.resolved_at is None

    finally:
        db.rollback()
        db.close()


def test_investigating_can_be_resolved():
    db, incident = create_test_incident(INVESTIGATING)

    try:
        updated = resolve_incident(
            db=db,
            incident=incident,
        )

        assert updated.status == RESOLVED
        assert updated.resolved_at is not None

    finally:
        db.rollback()
        db.close()


def test_open_can_be_resolved_directly():
    db, incident = create_test_incident(OPEN)

    try:
        updated = resolve_incident(
            db=db,
            incident=incident,
        )

        assert updated.status == RESOLVED
        assert updated.resolved_at is not None

    finally:
        db.rollback()
        db.close()


def test_resolved_cannot_start_investigation():
    db, incident = create_test_incident(RESOLVED)

    try:
        with pytest.raises(ValueError):
            start_incident_investigation(
                db=db,
                incident=incident,
            )

    finally:
        db.rollback()
        db.close()


def test_resolved_cannot_be_resolved_again():
    db, incident = create_test_incident(RESOLVED)

    try:
        with pytest.raises(ValueError):
            resolve_incident(
                db=db,
                incident=incident,
            )

    finally:
        db.rollback()
        db.close()


def test_investigating_cannot_start_investigation_again():
    db, incident = create_test_incident(INVESTIGATING)

    try:
        with pytest.raises(ValueError):
            start_incident_investigation(
                db=db,
                incident=incident,
            )

    finally:
        db.rollback()
        db.close()


def test_resolve_sets_resolved_at():
    db, incident = create_test_incident(OPEN)

    try:
        before_resolution = datetime.now(timezone.utc)

        updated = resolve_incident(
            db=db,
            incident=incident,
        )

        after_resolution = datetime.now(timezone.utc)

        assert updated.resolved_at is not None
        assert before_resolution <= updated.resolved_at
        assert updated.resolved_at <= after_resolution

    finally:
        db.rollback()
        db.close()


def test_start_investigation_does_not_set_resolved_at():
    db, incident = create_test_incident(OPEN)

    try:
        updated = start_incident_investigation(
            db=db,
            incident=incident,
        )

        assert updated.status == INVESTIGATING
        assert updated.resolved_at is None

    finally:
        db.rollback()
        db.close()