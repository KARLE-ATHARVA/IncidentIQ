from fastapi.testclient import TestClient

from backend.app.main import app
from uuid import uuid4


client = TestClient(app)


def test_register_and_login():
    email = f"testuser-{uuid4()}@example.com"
    password = "testpassword123"

    # Register
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_endpoint_requires_authentication():
    response = client.get("/api/auth/me")

    assert response.status_code == 401