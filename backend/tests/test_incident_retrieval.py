from datetime import datetime, timezone
from uuid import uuid4

from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.incident_retrieval import (
    build_incident_embedding_text,
)

from unittest.mock import patch

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.services.incident_retrieval import (
    retrieve_historical_context,
)


def test_build_incident_embedding_text():
    incident = Incident(
        id=uuid4(),
        project_id=uuid4(),
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status="open",
        detected_at=datetime.now(timezone.utc),
    )

    text = build_incident_embedding_text(incident)

    assert "Current Incident" in text
    assert "Title: Checkout latency incident" in text
    assert "Description: Checkout latency increased significantly." in text
    assert "Severity: high" in text
    assert "Status: open" in text




def test_retrieve_historical_context(
    db_session,
):
    project_id = uuid4()
    service_id = uuid4()

    user = User(
        email=f"retrieval-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db_session.add(user)
    db_session.flush()

    project = Project(
        id=project_id,
        name="Incident Retrieval Project",
        owner_id=user.id,
    )
    db_session.add(project)
    db_session.flush()

    service = Service(
        id=service_id,
        name="checkout",
        project_id=project_id,
    )
    db_session.add(service)
    db_session.flush()

    incident = Incident(
        id=uuid4(),
        project_id=project_id,
        title="Checkout latency incident",
        description="Checkout latency increased.",
        severity="high",
        status="open",
        detected_at=datetime.now(timezone.utc),
    )

    historical = HistoricalIncident(
        id=uuid4(),
        incident_id=incident.id,
        project_id=project_id,
        service_id=service_id,
        title="Previous checkout latency incident",
        summary="Checkout latency increased.",
        symptoms="Slow checkout requests.",
        root_cause="Database connection exhaustion",
        resolution="Increased connection pool.",
        severity="high",
        occurred_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )

    db_session.add(incident)
    db_session.flush()
    db_session.add(historical)
    db_session.commit()

    historical_embedding = HistoricalIncidentEmbedding(
        historical_incident_id=historical.id,
        embedding=[1.0] + [0.0] * 383,
        model_name="all-MiniLM-L6-v2",
        embedding_text="Previous checkout latency incident",
    )

    db_session.add(historical_embedding)
    db_session.commit()

    with patch(
        "backend.app.services.incident_retrieval.generate_embedding",
        return_value=[1.0] + [0.0] * 383,
    ):
        results = retrieve_historical_context(
            db=db_session,
            incident=incident,
            top_k=5,
        )

    assert len(results) == 1
    assert results[0].historical_incident_id == historical.id
    assert results[0].similarity_score == 1.0