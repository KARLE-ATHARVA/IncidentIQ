import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.core.security import hash_password


client = TestClient(app)


def create_user():
    db = SessionLocal()

    user = User(
        email=f"investigation-{uuid.uuid4()}@example.com",
        password_hash=hash_password("Password123!"),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.close()

    return user


def create_project(user):
    db = SessionLocal()

    project = Project(
        name=f"Investigation Project {uuid.uuid4()}",
        owner_id=user.id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    db.close()

    return project


def create_service(project):
    db = SessionLocal()

    service = Service(
        name=f"checkout-{uuid.uuid4()}",
        project_id=project.id,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    db.close()

    return service


def create_incident(project):
    db = SessionLocal()

    incident = Incident(
        project_id=project.id,
        title="Checkout service incident",
        description="Checkout latency increased.",
        severity="high",
        status="open",
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    db.close()

    return incident


def login_user(user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_test_context():
    user = create_user()
    project = create_project(user)
    service = create_service(project)
    incident = create_incident(project)
    token = login_user(user)

    return user, project, service, incident, token


def create_investigation_directly(incident_id, status="pending"):
    db = SessionLocal()

    investigation = Investigation(
        incident_id=incident_id,
        status=status,
    )

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    db.close()

    return investigation


# ---------------------------------------------------------
# 1. Create investigation
# ---------------------------------------------------------


def test_create_investigation():
    _, project, _, incident, token = create_test_context()

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}/investigations",
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["incident_id"] == str(incident.id)
    assert data["status"] == "pending"
    assert data["started_at"] is None
    assert data["completed_at"] is None


# ---------------------------------------------------------
# 2. Start investigation
# ---------------------------------------------------------


def test_start_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="pending",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/start",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(investigation.id)
    assert data["status"] == "running"
    assert data["started_at"] is not None
    assert data["completed_at"] is None


# ---------------------------------------------------------
# 3. Complete investigation
# ---------------------------------------------------------


def test_complete_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="running",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/complete",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(investigation.id)
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


# ---------------------------------------------------------
# 4. Fail investigation
# ---------------------------------------------------------


def test_fail_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="running",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/fail",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(investigation.id)
    assert data["status"] == "failed"
    assert data["completed_at"] is not None


# ---------------------------------------------------------
# 5. Cannot start twice
# ---------------------------------------------------------


def test_cannot_start_running_investigation_twice():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="running",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/start",
        headers=auth_headers(token),
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# 6. Cannot complete pending investigation
# ---------------------------------------------------------


def test_cannot_complete_pending_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="pending",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/complete",
        headers=auth_headers(token),
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# 7. Cannot complete completed investigation
# ---------------------------------------------------------


def test_cannot_complete_completed_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="completed",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/complete",
        headers=auth_headers(token),
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# 8. Cannot fail pending investigation
# ---------------------------------------------------------


def test_cannot_fail_pending_investigation():
    _, project, _, incident, token = create_test_context()

    investigation = create_investigation_directly(
        incident.id,
        status="pending",
    )

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/fail",
        headers=auth_headers(token),
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# 9. Authorization
# ---------------------------------------------------------


def test_another_user_cannot_access_investigation():
    owner = create_user()
    owner_project = create_project(owner)
    create_service(owner_project)
    incident = create_incident(owner_project)

    investigation = create_investigation_directly(
        incident.id,
        status="pending",
    )

    other_user = create_user()
    other_project = create_project(other_user)
    other_token = login_user(other_user)

    response = client.post(
        f"/api/projects/{other_project.id}/incidents/{incident.id}"
        f"/investigations/{investigation.id}/start",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# 10. Wrong incident
# ---------------------------------------------------------


def test_investigation_cannot_be_accessed_through_wrong_incident():
    user = create_user()
    project = create_project(user)

    incident_a = create_incident(project)
    incident_b = create_incident(project)

    investigation = create_investigation_directly(
        incident_a.id,
        status="pending",
    )

    token = login_user(user)

    response = client.post(
        f"/api/projects/{project.id}/incidents/{incident_b.id}"
        f"/investigations/{investigation.id}/start",
        headers=auth_headers(token),
    )

    assert response.status_code == 404