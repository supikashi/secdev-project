import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import engine, metadata  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="function")
def test_db():
    metadata.create_all(bind=engine)
    yield engine
    metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    from app.main import _RATE_LIMIT, _RATE_LIMIT_IP, _TOKENS

    _TOKENS.clear()
    _RATE_LIMIT.clear()
    _RATE_LIMIT_IP.clear()

    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    def _auth_headers(username="testuser", password="testpass123"):
        response = client.post(
            "/auth/register", params={"username": username, "password": password}
        )
        assert response.status_code == 200

        response = client.post(
            "/auth/login", params={"username": username, "password": password}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
