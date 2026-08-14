import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_ROOT = Path(__file__).parent / ".data"
os.environ.update(
    {
        "DATABASE_URL": f"sqlite:///{TEST_ROOT / 'test.db'}",
        "DATA_ROOT": str(TEST_ROOT),
        "HOST_DATA_ROOT": str(TEST_ROOT),
        "JWT_SECRET": "test-jwt-secret",
        "CREDENTIAL_ENCRYPTION_KEY": "test-encryption-secret",
        "BOOTSTRAP_ADMIN_PASSWORD": "AdminPassword123!",
        "MIN_FREE_DISK_GB": "0",
    }
)

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
