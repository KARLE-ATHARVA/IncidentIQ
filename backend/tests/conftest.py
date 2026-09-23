import pytest

from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal


@pytest.fixture
def db_session():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def auth_headers():
    def build_headers(user):
        token = create_access_token(str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return build_headers
