import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings

os.environ.setdefault("JWT_SECRET", "collection-secret-that-is-long-enough")
os.environ.setdefault("ADMIN_PASSWORD", "collection-password")
os.environ.setdefault("PRIVATE_DATABASE_URL", "sqlite:///collection-private.sqlite3")
os.environ.setdefault("CLOUD_DATABASE_URL", "sqlite:///collection-cloud.sqlite3")


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    from app.main import create_app

    settings = Settings(
        jwt_secret="test-secret-that-is-long-enough-for-validation",
        admin_username="tester",
        admin_password="test-password",
        private_database_url=f"sqlite:///{tmp_path / 'private.sqlite3'}",
        cloud_database_url=f"sqlite:///{tmp_path / 'cloud.sqlite3'}",
        auto_create_schema=True,
        seed_demo_data=False,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token", data={"username": "tester", "password": "test-password"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
