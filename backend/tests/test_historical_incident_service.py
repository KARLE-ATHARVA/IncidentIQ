from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.db.database import SessionLocal
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.services.historical_incident import (
    create_historical_incident,
)


def create_test_incident(status="resolved"):
    db = SessionLocal()

    user = User(
        email=f"historical-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        name=f"Historical Project {uuid4()}",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Latency increased significantly.",
        severity="high",
        status=status,
        detected_at=datetime(
            2026,
            9,
            9,
            0,
            7,
            10,
            tzinfo=timezone.utc,
        ),
        resolved_at=(
            datetime(
                2026,
                9,
                9,
                0,
                20,
                10,
                tzinfo=timezone.utc,
            )
            if status == "resolved"
            else None
        ),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return db, incident


def test_create_historical_incident_from_resolved_incident():
    db, incident = create_test_incident()

    try:
        historical = create_historical_incident(
            db=db,
            incident=incident,
            title="Checkout latency incident",
            summary="Checkout latency increased significantly.",
            symptoms="High latency and payment timeout errors.",
            root_cause="Payment service timeout.",
            resolution="Rolled back deployment v2.4.0.",
        )

        assert historical.id is not None
        assert historical.incident_id == incident.id
        assert historical.project_id == incident.project_id
        assert historical.title == "Checkout latency incident"
        assert historical.root_cause == "Payment service timeout."
        assert historical.resolution == (
            "Rolled back deployment v2.4.0."
        )
        assert historical.severity == incident.severity
        assert historical.occurred_at == incident.detected_at
        assert historical.resolved_at == incident.resolved_at

    finally:
        db.rollback()
        db.close()


def test_historical_incident_allows_unknown_root_cause():
    db, incident = create_test_incident()

    try:
        historical = create_historical_incident(
            db=db,
            incident=incident,
            title="Checkout latency incident",
            summary="Checkout latency increased.",
            symptoms="Elevated checkout latency.",
        )

        assert historical.root_cause is None
        assert historical.resolution is None

    finally:
        db.rollback()
        db.close()


def test_cannot_create_historical_incident_from_open_incident():
    db, incident = create_test_incident(status="open")

    try:
        with pytest.raises(
            ValueError,
            match="Only resolved incidents",
        ):
            create_historical_incident(
                db=db,
                incident=incident,
                title="Checkout latency incident",
                summary="Checkout latency increased.",
                symptoms="Elevated checkout latency.",
            )

    finally:
        db.rollback()
        db.close()


def test_cannot_create_duplicate_historical_incident():
    db, incident = create_test_incident()

    try:
        create_historical_incident(
            db=db,
            incident=incident,
            title="Checkout latency incident",
            summary="Checkout latency increased.",
            symptoms="Elevated checkout latency.",
        )

        with pytest.raises(
            ValueError,
            match="already exists",
        ):
            create_historical_incident(
                db=db,
                incident=incident,
                title="Duplicate historical record",
                summary="Another summary.",
                symptoms="Another symptom.",
            )

    finally:
        db.rollback()
        db.close()


def test_historical_incident_rejects_empty_title():
    db, incident = create_test_incident()

    try:
        with pytest.raises(
            ValueError,
            match="title cannot be empty",
        ):
            create_historical_incident(
                db=db,
                incident=incident,
                title="   ",
                summary="Valid summary.",
                symptoms="Valid symptoms.",
            )

    finally:
        db.rollback()
        db.close()


def test_historical_incident_rejects_empty_summary():
    db, incident = create_test_incident()

    try:
        with pytest.raises(
            ValueError,
            match="summary cannot be empty",
        ):
            create_historical_incident(
                db=db,
                incident=incident,
                title="Valid title",
                summary="   ",
                symptoms="Valid symptoms.",
            )

    finally:
        db.rollback()
        db.close()


def test_historical_incident_rejects_empty_symptoms():
    db, incident = create_test_incident()

    try:
        with pytest.raises(
            ValueError,
            match="symptoms cannot be empty",
        ):
            create_historical_incident(
                db=db,
                incident=incident,
                title="Valid title",
                summary="Valid summary.",
                symptoms="   ",
            )

    finally:
        db.rollback()
        db.close()