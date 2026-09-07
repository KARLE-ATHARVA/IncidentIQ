from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.core.security import create_access_token


client = TestClient(app)


def create_user_project():
    db = SessionLocal()

    user = User(
        email=f"incident-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )

    db.add(user)
    db.flush()

    project = Project(
        name=f"Incident API Project {uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.commit()
    db.refresh(user)
    db.refresh(project)

    return db, user, project


def create_token(user_id):
    return create_access_token(str(user_id))


def test_list_incidents():
    db, user, project = create_user_project()

    try:
        incident = Incident(
            project_id=project.id,
            title="Checkout latency incident",
            description="Latency increased significantly.",
            severity="high",
            status="open",
            detected_at=datetime.now(timezone.utc),
        )

        db.add(incident)
        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(incident.id)
        assert data["items"][0]["severity"] == "high"
        assert data["items"][0]["status"] == "open"

    finally:
        db.rollback()
        db.close()


def test_get_incident():
    db, user, project = create_user_project()

    try:
        incident = Incident(
            project_id=project.id,
            title="Payment failure",
            description="Payment provider errors detected.",
            severity="critical",
            status="investigating",
            detected_at=datetime.now(timezone.utc),
        )

        db.add(incident)
        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(incident.id)
        assert data["project_id"] == str(project.id)
        assert data["severity"] == "critical"
        assert data["status"] == "investigating"

    finally:
        db.rollback()
        db.close()


def test_list_incidents_filters_by_status():
    db, user, project = create_user_project()

    try:
        now = datetime.now(timezone.utc)

        db.add_all(
            [
                Incident(
                    project_id=project.id,
                    title="Open incident",
                    description="Open",
                    severity="high",
                    status="open",
                    detected_at=now,
                ),
                Incident(
                    project_id=project.id,
                    title="Resolved incident",
                    description="Resolved",
                    severity="high",
                    status="resolved",
                    detected_at=now - timedelta(minutes=1),
                ),
            ]
        )

        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            params={"status": "open"},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert data["items"][0]["status"] == "open"

    finally:
        db.rollback()
        db.close()


def test_list_incidents_filters_by_severity():
    db, user, project = create_user_project()

    try:
        now = datetime.now(timezone.utc)

        db.add_all(
            [
                Incident(
                    project_id=project.id,
                    title="Critical incident",
                    description="Critical",
                    severity="critical",
                    status="open",
                    detected_at=now,
                ),
                Incident(
                    project_id=project.id,
                    title="Medium incident",
                    description="Medium",
                    severity="medium",
                    status="open",
                    detected_at=now - timedelta(minutes=1),
                ),
            ]
        )

        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            params={"severity": "critical"},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert data["items"][0]["severity"] == "critical"

    finally:
        db.rollback()
        db.close()


def test_incidents_are_ordered_newest_first():
    db, user, project = create_user_project()

    try:
        now = datetime.now(timezone.utc)

        older = Incident(
            project_id=project.id,
            title="Older incident",
            description="Older",
            severity="medium",
            status="open",
            detected_at=now - timedelta(minutes=10),
        )

        newer = Incident(
            project_id=project.id,
            title="Newer incident",
            description="Newer",
            severity="high",
            status="open",
            detected_at=now,
        )

        db.add_all([older, newer])
        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["items"][0]["id"] == str(newer.id)
        assert data["items"][1]["id"] == str(older.id)

    finally:
        db.rollback()
        db.close()


def test_incident_date_filter():
    db, user, project = create_user_project()

    try:
        now = datetime.now(timezone.utc)

        older = Incident(
            project_id=project.id,
            title="Old incident",
            description="Old",
            severity="medium",
            status="open",
            detected_at=now - timedelta(hours=2),
        )

        recent = Incident(
            project_id=project.id,
            title="Recent incident",
            description="Recent",
            severity="high",
            status="open",
            detected_at=now - timedelta(minutes=10),
        )

        db.add_all([older, recent])
        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            params={
                "start_time": (
                    now - timedelta(hours=1)
                ).isoformat()
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert data["items"][0]["id"] == str(recent.id)

    finally:
        db.rollback()
        db.close()


def test_incident_limit():
    db, user, project = create_user_project()

    try:
        now = datetime.now(timezone.utc)

        for index in range(5):
            db.add(
                Incident(
                    project_id=project.id,
                    title=f"Incident {index}",
                    description="Test",
                    severity="medium",
                    status="open",
                    detected_at=now - timedelta(minutes=index),
                )
            )

        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            params={"limit": 2},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 2
        assert len(data["items"]) == 2

    finally:
        db.rollback()
        db.close()


def test_unauthenticated_request_is_rejected():
    db, user, project = create_user_project()

    try:
        response = client.get(
            f"/api/projects/{project.id}/incidents"
        )

        assert response.status_code == 401

    finally:
        db.rollback()
        db.close()


def test_user_cannot_access_another_users_project():
    db, owner, project = create_user_project()

    try:
        other_user = User(
            email=f"other-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(other_user)
        db.commit()

        token = create_token(other_user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

    finally:
        db.rollback()
        db.close()


def test_incident_from_another_project_is_not_accessible():
    db, user, project = create_user_project()

    try:
        other_project = Project(
            name=f"Other Project {uuid4()}",
            owner_id=user.id,
        )

        db.add(other_project)
        db.flush()

        incident = Incident(
            project_id=other_project.id,
            title="Private incident",
            description="Should not be accessible.",
            severity="high",
            status="open",
            detected_at=datetime.now(timezone.utc),
        )

        db.add(incident)
        db.commit()

        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{incident.id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

    finally:
        db.rollback()
        db.close()


def test_nonexistent_incident_returns_404():
    db, user, project = create_user_project()

    try:
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents/{uuid4()}",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

    finally:
        db.rollback()
        db.close()


def test_invalid_limit_is_rejected():
    db, user, project = create_user_project()

    try:
        token = create_token(user.id)

        response = client.get(
            f"/api/projects/{project.id}/incidents",
            params={"limit": 501},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        db.rollback()
        db.close()
