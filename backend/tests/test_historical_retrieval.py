from datetime import datetime, timezone
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
from backend.app.services.historical_retrieval import (
    retrieve_similar_historical_incidents,
)


def create_historical_incident(
    db_session,
    project_id,
    service_id,
    title,
    embedding,
):
    project = db_session.get(Project, project_id)
    if project is None:
        user = User(
            email=f"retrieval-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db_session.add(user)
        db_session.flush()

        project = Project(
            id=project_id,
            name=f"Retrieval Project {uuid4()}",
            owner_id=user.id,
        )
        db_session.add(project)
        db_session.flush()

    service = db_session.get(Service, service_id)
    if service is None:
        service = Service(
            id=service_id,
            name="checkout",
            project_id=project_id,
        )
        db_session.add(service)
        db_session.flush()

    incident_id = uuid4()
    incident = Incident(
        id=incident_id,
        project_id=project_id,
        title=title,
        description="Test incident",
        severity="high",
        status="resolved",
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.flush()

    incident = HistoricalIncident(
        id=uuid4(),
        incident_id=incident_id,
        project_id=project_id,
        service_id=service_id,
        title=title,
        summary="Test summary",
        symptoms="Test symptoms",
        root_cause="Test root cause",
        resolution="Test resolution",
        severity="high",
        occurred_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )

    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    embedding_record = HistoricalIncidentEmbedding(
        historical_incident_id=incident.id,
        embedding=embedding,
        model_name="all-MiniLM-L6-v2",
        embedding_text=f"Historical Incident\nTitle: {title}",
    )

    db_session.add(embedding_record)
    db_session.commit()

    return incident


def test_retrieves_most_similar_incident_first(db_session):
    project_id = uuid4()
    service_id = uuid4()

    similar = create_historical_incident(
        db_session,
        project_id,
        service_id,
        "Checkout latency incident",
        [1.0] + [0.0] * 383,
    )

    different = create_historical_incident(
        db_session,
        project_id,
        service_id,
        "Authentication failure incident",
        [0.0, 1.0] + [0.0] * 382,
    )

    query_embedding = [1.0] + [0.0] * 383

    results = retrieve_similar_historical_incidents(
        db=db_session,
        project_id=project_id,
        query_embedding=query_embedding,
        top_k=5,
    )

    assert len(results) == 2
    assert results[0].historical_incident_id == similar.id
    assert results[0].similarity_score > results[1].similarity_score


def test_retrieval_is_isolated_by_project(db_session):
    project_a = uuid4()
    project_b = uuid4()
    service_id = uuid4()

    incident_a = create_historical_incident(
        db_session,
        project_a,
        service_id,
        "Project A incident",
        [1.0] + [0.0] * 383,
    )

    create_historical_incident(
        db_session,
        project_b,
        service_id,
        "Project B incident",
        [1.0] + [0.0] * 383,
    )

    results = retrieve_similar_historical_incidents(
        db=db_session,
        project_id=project_a,
        query_embedding=[1.0] + [0.0] * 383,
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].historical_incident_id == incident_a.id


def test_top_k_is_respected(db_session):
    project_id = uuid4()
    service_id = uuid4()

    for index in range(5):
        create_historical_incident(
            db_session,
            project_id,
            service_id,
            f"Incident {index}",
            [1.0] + [0.0] * 383,
        )

    results = retrieve_similar_historical_incidents(
        db=db_session,
        project_id=project_id,
        query_embedding=[1.0] + [0.0] * 383,
        top_k=2,
    )

    assert len(results) == 2


def test_invalid_top_k_is_rejected(db_session):
    with pytest.raises(ValueError, match="greater than zero"):
        retrieve_similar_historical_incidents(
            db=db_session,
            project_id=uuid4(),
            query_embedding=[1.0] + [0.0] * 383,
            top_k=0,
        )


def test_top_k_limit_is_rejected(db_session):
    with pytest.raises(ValueError, match="cannot exceed 20"):
        retrieve_similar_historical_incidents(
            db=db_session,
            project_id=uuid4(),
            query_embedding=[1.0] + [0.0] * 383,
            top_k=21,
        )