from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User


client = TestClient(app)


def create_user_project():
    db = SessionLocal()

    user = User(
        email=f"historical-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        name=f"Historical API Project {uuid4()}",
        owner_id=user.id,
    )
    db.add(project)
    db.commit()

    db.refresh(user)
    db.refresh(project)

    return db, user, project


def create_token(user_id):
    return create_access_token(str(user_id))


def create_incident(db, project, status="resolved"):
    now = datetime.now(timezone.utc)

    incident = Incident(
        project_id=project.id,
        title="Checkout latency incident",
        description="Checkout latency increased significantly.",
        severity="high",
        status=status,
        detected_at=now,
        resolved_at=now if status == "resolved" else None,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def create_historical_incident(db, project, incident, title):
    historical = HistoricalIncident(
        incident_id=incident.id,
        project_id=project.id,
        title=title,
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


def test_create_historical_record_requires_authentication():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        response = client.post(
            f"/api/projects/{project.id}/incidents/{incident.id}/historical-record",
            json={
                "title": "Checkout latency incident",
                "summary": "Checkout latency increased.",
                "symptoms": "Elevated latency and timeout errors.",
            },
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_create_historical_record_success():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)
        token = create_token(user.id)

        response = client.post(
            f"/api/projects/{project.id}/incidents/{incident.id}/historical-record",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "title": "Checkout latency incident",
                "summary": "Checkout latency increased significantly.",
                "symptoms": "High latency and payment timeout errors.",
                "root_cause": "Payment service timeout.",
                "resolution": "Rolled back deployment v2.4.0.",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["incident_id"] == str(incident.id)
        assert data["project_id"] == str(project.id)
        assert data["title"] == "Checkout latency incident"
        assert data["summary"] == (
            "Checkout latency increased significantly."
        )
        assert data["symptoms"] == (
            "High latency and payment timeout errors."
        )
        assert data["root_cause"] == "Payment service timeout."
        assert data["resolution"] == "Rolled back deployment v2.4.0."
        assert data["severity"] == "high"

    finally:
        db.rollback()
        db.close()


def test_create_historical_record_rejects_unknown_project():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)
        token = create_token(user.id)

        other_project_id = uuid4()

        response = client.post(
            f"/api/projects/{other_project_id}/incidents/{incident.id}/historical-record",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "title": "Checkout latency incident",
                "summary": "Checkout latency increased.",
                "symptoms": "Elevated latency.",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found."

    finally:
        db.rollback()
        db.close()


def test_create_historical_record_rejects_unknown_incident():
    db, user, project = create_user_project()

    try:
        token = create_token(user.id)

        response = client.post(
            f"/api/projects/{project.id}/incidents/{uuid4()}/historical-record",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "title": "Checkout latency incident",
                "summary": "Checkout latency increased.",
                "symptoms": "Elevated latency.",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Incident not found."

    finally:
        db.rollback()
        db.close()


def test_create_historical_record_maps_service_error_to_bad_request():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project, status="open")
        token = create_token(user.id)

        response = client.post(
            f"/api/projects/{project.id}/incidents/{incident.id}/historical-record",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "title": "Checkout latency incident",
                "summary": "Checkout latency increased.",
                "symptoms": "Elevated latency.",
            },
        )

        assert response.status_code == 400
        assert "Only resolved incidents" in response.json()["detail"]

    finally:
        db.rollback()
        db.close()


def test_list_historical_incidents_requires_authentication():
    db, user, project = create_user_project()

    try:
        response = client.get(
            f"/api/projects/{project.id}/historical-incidents"
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_list_historical_incidents_returns_project_records():
    db, user, project = create_user_project()

    try:
        incident_one = create_incident(db, project)
        incident_two = create_incident(db, project)

        create_historical_incident(
            db,
            project,
            incident_one,
            "Older checkout incident",
        )

        create_historical_incident(
            db,
            project,
            incident_two,
            "Newer checkout incident",
        )

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/historical-incidents",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2
        assert data[0]["title"] == "Newer checkout incident"
        assert data[1]["title"] == "Older checkout incident"

    finally:
        db.rollback()
        db.close()


def test_list_historical_incidents_rejects_unknown_project():
    db, user, project = create_user_project()

    try:
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{uuid4()}/historical-incidents",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found."

    finally:
        db.rollback()
        db.close()


def test_get_historical_incident_requires_authentication():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
            "Checkout historical incident",
        )

        response = client.get(
            f"/api/projects/{project.id}/historical-incidents/{historical.id}"
        )

        assert response.status_code in (401, 403)

    finally:
        db.rollback()
        db.close()


def test_get_historical_incident_returns_record():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
            "Checkout historical incident",
        )

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/historical-incidents/{historical.id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(historical.id)
        assert data["incident_id"] == str(incident.id)
        assert data["project_id"] == str(project.id)
        assert data["title"] == "Checkout historical incident"
        assert data["root_cause"] == "Database connection saturation."
        assert data["resolution"] == (
            "Increased database connection capacity."
        )

    finally:
        db.rollback()
        db.close()


def test_get_historical_incident_returns_not_found_for_unknown_record():
    db, user, project = create_user_project()

    try:
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/historical-incidents/{uuid4()}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Historical incident not found."
        )

    finally:
        db.rollback()
        db.close()


def test_get_historical_incident_rejects_unknown_project():
    db, user, project = create_user_project()

    try:
        incident = create_incident(db, project)

        historical = create_historical_incident(
            db,
            project,
            incident,
            "Checkout historical incident",
        )

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{uuid4()}/historical-incidents/{historical.id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found."

    finally:
        db.rollback()
        db.close()