from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User


client = TestClient(app)


def create_user_project():
    db = SessionLocal()

    user = User(
        email=f"retrieval-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"Retrieval API Project {uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.commit()

    db.refresh(user)
    db.refresh(project)

    return db, user, project


def create_token(user_id):
    return create_access_token(str(user_id))


def create_incident(db, project):
    now = datetime.now(timezone.utc)

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status="resolved",
        detected_at=now,
        resolved_at=now,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def create_historical_incident(db, project, incident, title=None):
    source_incident = Incident(
        project_id=project.id,
        title=title or "Previous checkout latency incident",
        description="Historical source incident.",
        severity="high",
        status="resolved",
        detected_at=incident.detected_at,
        resolved_at=incident.resolved_at,
    )
    db.add(source_incident)
    db.flush()

    historical = HistoricalIncident(
        incident_id=source_incident.id,
        project_id=project.id,
        title=title or "Previous checkout latency incident",
        summary="Checkout latency increased during a previous incident.",
        symptoms="Elevated checkout latency and error logs.",
        root_cause="Database connection saturation.",
        resolution="Increased database connection capacity.",
        severity="high",
        occurred_at=incident.detected_at,
        resolved_at=incident.resolved_at,
    )

    db.add(historical)
    db.commit()
    db.refresh(historical)

    return historical


def create_embedding(db, historical_incident, embedding):
    record = HistoricalIncidentEmbedding(
        historical_incident_id=historical_incident.id,
        embedding=embedding,
        model_name="test-model",
        embedding_text="test historical incident",
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def test_similar_historical_incidents_requires_auth():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents"
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_similar_historical_incidents_returns_results():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
        )

        create_embedding(
            db,
            historical,
            [0.1] * 384,
        )

        token = create_token(user.id)

        with patch(
            "backend.app.services.incident_retrieval.generate_embedding",
            return_value=[0.1] * 384,
        ):
            response = client.get(
                f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["historical_incident_id"] == str(historical.id)
        assert data[0]["title"] == "Previous checkout latency incident"
        assert data[0]["severity"] == "high"
        assert 0.0 <= data[0]["similarity_score"] <= 1.0

    finally:
        db.rollback()
        db.close()


def test_default_similarity_threshold_filters_weak_matches():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        strong_match = create_historical_incident(
            db,
            project,
            incident,
            title="Strong checkout match",
        )

        weak_match = create_historical_incident(
            db,
            project,
            incident,
            title="Weak unrelated match",
        )

        query_embedding = [1.0] + [0.0] * 383

        create_embedding(
            db,
            strong_match,
            query_embedding,
        )

        create_embedding(
            db,
            weak_match,
            [0.0, 1.0] + [0.0] * 382,
        )

        token = create_token(user.id)

        with patch(
            "backend.app.services.incident_retrieval.generate_embedding",
            return_value=query_embedding,
        ):
            response = client.get(
                f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["historical_incident_id"] == str(
            strong_match.id
        )
        assert data[0]["similarity_score"] >= 0.65

        assert all(
            item["historical_incident_id"] != str(weak_match.id)
            for item in data
        )

    finally:
        db.rollback()
        db.close()


def test_custom_similarity_threshold_is_applied():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
            title="Checkout historical incident",
        )

        query_embedding = [1.0] + [0.0] * 383

        create_embedding(
            db,
            historical,
            query_embedding,
        )

        token = create_token(user.id)

        with patch(
            "backend.app.services.incident_retrieval.generate_embedding",
            return_value=query_embedding,
        ):
            response = client.get(
                f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents"
                "?similarity_threshold=1.0",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["historical_incident_id"] == str(
            historical.id
        )
        assert data[0]["similarity_score"] == 1.0

    finally:
        db.rollback()
        db.close()


def test_similarity_threshold_can_exclude_all_results():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
        )

        query_embedding = [1.0] + [0.0] * 383

        create_embedding(
            db,
            historical,
            query_embedding,
        )

        token = create_token(user.id)

        with patch(
            "backend.app.services.incident_retrieval.generate_embedding",
            return_value=query_embedding,
        ):
            response = client.get(
                f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents"
                "?similarity_threshold=1.1",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 422

    finally:
        db.rollback()
        db.close()


def test_similar_historical_incidents_are_project_scoped():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
        )

        create_embedding(
            db,
            historical,
            [0.1] * 384,
        )

        other_user = User(
            email=f"other-retrieval-api-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(other_user)
        db.flush()

        other_project = Project(
            name=f"Other Retrieval Project {uuid4()}",
            owner_id=other_user.id,
        )

        db.add(other_project)
        db.commit()

        other_incident = create_incident(
            db,
            other_project,
        )

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{other_project.id}/incidents/{other_incident.id}/similar-incidents",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

    finally:
        db.rollback()
        db.close()


def test_similar_historical_incidents_rejects_top_k_above_20():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents"
            "?top_k=21",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        db.rollback()
        db.close()


def test_similar_historical_incidents_rejects_top_k_zero():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}/similar-incidents"
            "?top_k=0",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        db.rollback()
        db.close()