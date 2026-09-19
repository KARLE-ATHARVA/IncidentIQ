from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.historical_incident_embedding import (
    create_historical_incident_embedding,
)


def make_historical_incident(db_session) -> HistoricalIncident:
    user = User(
        email=f"embedding-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db_session.add(user)
    db_session.flush()

    project = Project(
        name=f"Embedding Project {uuid4()}",
        owner_id=user.id,
    )
    db_session.add(project)
    db_session.flush()

    service = Service(
        name="checkout",
        project_id=project.id,
    )
    db_session.add(service)
    db_session.flush()

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status="resolved",
        detected_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.flush()

    return HistoricalIncident(
        id=uuid4(),
        incident_id=incident.id,
        project_id=project.id,
        service_id=service.id,
        title="Checkout latency incident",
        summary="Checkout latency increased significantly.",
        symptoms="High checkout latency and increased error logs.",
        root_cause="Database connection pool exhaustion",
        resolution="Increased connection pool capacity.",
        severity="high",
        occurred_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        resolved_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )


def test_create_historical_incident_embedding(db_session):
    historical_incident = make_historical_incident(db_session)

    db_session.add(historical_incident)
    db_session.commit()
    db_session.refresh(historical_incident)

    fake_embedding = [0.1] * 384

    with patch(
        "backend.app.services.historical_incident_embedding.generate_embedding",
        return_value=fake_embedding,
    ):
        result = create_historical_incident_embedding(
            db=db_session,
            historical_incident=historical_incident,
        )

    assert result.historical_incident_id == historical_incident.id
    assert len(result.embedding) == 384
    assert result.model_name == "all-MiniLM-L6-v2"
    assert "Checkout latency incident" in result.embedding_text

    stored = (
        db_session.query(HistoricalIncidentEmbedding)
        .filter(
            HistoricalIncidentEmbedding.historical_incident_id
            == historical_incident.id
        )
        .first()
    )

    assert stored is not None
    assert len(stored.embedding) == 384


def test_create_historical_incident_embedding_rejects_duplicate(
    db_session,
):
    historical_incident = make_historical_incident(db_session)

    db_session.add(historical_incident)
    db_session.commit()
    db_session.refresh(historical_incident)

    fake_embedding = [0.1] * 384

    with patch(
        "backend.app.services.historical_incident_embedding.generate_embedding",
        return_value=fake_embedding,
    ):
        create_historical_incident_embedding(
            db=db_session,
            historical_incident=historical_incident,
        )

    with pytest.raises(ValueError, match="embedding already exists"):
        create_historical_incident_embedding(
            db=db_session,
            historical_incident=historical_incident,
        )