from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_user_and_login():
    email = f"test-{uuid4()}@example.com"
    password = "testpassword123"

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_user_can_access_own_project():
    token = create_user_and_login()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create project
    create_response = client.post(
        "/api/projects",
        json={
            "name": "My Test Project"
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    project = create_response.json()

    # Access own project
    get_response = client.get(
        f"/api/projects/{project['id']}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == project["id"]


def test_user_cannot_access_another_users_project():
    user_a_token = create_user_and_login()
    user_b_token = create_user_and_login()

    user_a_headers = {
        "Authorization": f"Bearer {user_a_token}"
    }

    user_b_headers = {
        "Authorization": f"Bearer {user_b_token}"
    }

    # User A creates a project
    create_response = client.post(
        "/api/projects",
        json={
            "name": "User A Project"
        },
        headers=user_a_headers,
    )

    assert create_response.status_code == 201

    project_id = create_response.json()["id"]

    # User B attempts to access User A's project
    get_response = client.get(
        f"/api/projects/{project_id}",
        headers=user_b_headers,
    )

    assert get_response.status_code == 404


def test_user_cannot_access_another_users_service():
    user_a_token = create_user_and_login()
    user_b_token = create_user_and_login()

    user_a_headers = {
        "Authorization": f"Bearer {user_a_token}"
    }

    user_b_headers = {
        "Authorization": f"Bearer {user_b_token}"
    }

    # User A creates a project
    project_response = client.post(
        "/api/projects",
        json={
            "name": "Service Test Project"
        },
        headers=user_a_headers,
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # User A creates a service
    service_response = client.post(
        f"/api/projects/{project_id}/services",
        json={
            "name": "Checkout Service"
        },
        headers=user_a_headers,
    )

    assert service_response.status_code == 201

    service_id = service_response.json()["id"]

    # User B attempts to access User A's service
    get_response = client.get(
        f"/api/projects/{project_id}/services/{service_id}",
        headers=user_b_headers,
    )

    assert get_response.status_code == 404