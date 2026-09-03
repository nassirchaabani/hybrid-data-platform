from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="test PostgreSQL réservé à la CI ou à une exécution explicite",
)
def test_end_to_end_with_two_postgres_databases() -> None:
    settings = Settings(
        jwt_secret=os.environ["JWT_SECRET"],
        admin_username=os.environ["ADMIN_USERNAME"],
        admin_password=os.environ["ADMIN_PASSWORD"],
        private_database_url=os.environ["PRIVATE_DATABASE_URL"],
        cloud_database_url=os.environ["CLOUD_DATABASE_URL"],
        auto_create_schema=False,
        seed_demo_data=False,
    )

    with TestClient(create_app(settings)) as client:
        token = client.post(
            "/api/v1/auth/token",
            data={
                "username": settings.admin_username,
                "password": settings.admin_password.get_secret_value(),
            },
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        email = f"integration-{uuid4()}@example.org"
        member = client.post(
            "/api/v1/members",
            headers=headers,
            json={
                "full_name": "Test PostgreSQL",
                "email": email,
                "postal_code": "44000",
                "consent": True,
            },
        )
        assert member.status_code == 201
        participation = client.post(
            "/api/v1/participations",
            headers=headers,
            json={
                "member_ref": member.json()["id"],
                "program": "Permanence",
                "hours": 1.5,
            },
        )
        assert participation.status_code == 201
        private_tables = set(
            inspect(client.app.state.databases.private_engine).get_table_names()
        )
        cloud_tables = set(inspect(client.app.state.databases.cloud_engine).get_table_names())
        assert {"alembic_version", "members"} <= private_tables
        assert {"alembic_version", "participations"} <= cloud_tables
        assert "participations" not in private_tables
        assert "members" not in cloud_tables
