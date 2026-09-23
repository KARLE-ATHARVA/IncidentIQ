from datetime import datetime, timezone
from uuid import uuid4

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.services.historical_incident_embedding import (
    build_embedding_text,
)


def make_historical_incident(
    root_cause: str | None = None,
    resolution: str | None = None,
) -> HistoricalIncident:
    return HistoricalIncident(
        id=uuid4(),
        incident_id=uuid4(),
        project_id=uuid4(),
        service_id=uuid4(),
        title="Checkout latency incident",
        summary="Checkout latency increased significantly.",
        symptoms="High checkout latency and increased error logs.",
        root_cause=root_cause,
        resolution=resolution,
        severity="high",
        occurred_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )


def test_build_embedding_text_contains_historical_incident_fields():
    incident = make_historical_incident(
        root_cause="Database connection pool exhaustion",
        resolution="Increased connection pool capacity.",
    )

    text = build_embedding_text(incident)

    assert "Historical Incident" in text
    assert "Title: Checkout latency incident" in text
    assert "Summary: Checkout latency increased significantly." in text
    assert "Symptoms: High checkout latency and increased error logs." in text
    assert "Root Cause: Database connection pool exhaustion" in text
    assert "Resolution: Increased connection pool capacity." in text


def test_build_embedding_text_handles_unknown_root_cause_and_resolution():
    incident = make_historical_incident()

    text = build_embedding_text(incident)

    assert "Root Cause: Unknown" in text
    assert "Resolution: Unknown" in text

def test_historical_embedding_text_represents_reusable_incident_knowledge():
    incident = make_historical_incident(
        root_cause="Database connection pool exhaustion",
        resolution="Increased connection pool capacity.",
    )

    text = build_embedding_text(incident)

    required_knowledge = [
        "Summary:",
        "Symptoms:",
        "Root Cause:",
        "Resolution:",
    ]

    for field in required_knowledge:
        assert field in text