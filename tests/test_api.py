from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.config import Settings
from app.main import create_app


def _member(
    client: TestClient,
    headers: dict[str, str],
    email: str = "nora.diallo@example.org",
) -> dict:
    response = client.post(
        "/api/v1/members",
        headers=headers,
        json={
            "full_name": "Nora Diallo",
            "email": email,
            "postal_code": "35000",
            "consent": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_and_readiness(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"private": "ready", "cloud": "ready"}


def test_authentication_is_required(client: TestClient) -> None:
    assert client.get("/api/v1/members").status_code == 401
    assert client.post(
        "/api/v1/auth/token", data={"username": "tester", "password": "wrong"}
    ).status_code == 401

    settings = client.app.state.settings
    expired = jwt.encode(
        {"sub": "tester", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    assert client.get(
        "/api/v1/members", headers={"Authorization": f"Bearer {expired}"}
    ).status_code == 401


def test_data_is_physically_routed(client: TestClient, auth_headers: dict[str, str]) -> None:
    _member(client, auth_headers)
    databases = client.app.state.databases
    assert inspect(databases.private_engine).get_table_names() == ["members"]
    assert inspect(databases.cloud_engine).get_table_names() == ["participations"]


def test_federated_member_and_overview(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    member = _member(client, auth_headers)
    for program, hours in [("Maraude", 2.5), ("Atelier vélo", 4.0)]:
        response = client.post(
            "/api/v1/participations",
            headers=auth_headers,
            json={"member_ref": member["id"], "program": program, "hours": hours},
        )
        assert response.status_code == 201

    federated = client.get(
        f"/api/v1/federated/members/{member['id']}", headers=auth_headers
    )
    assert federated.status_code == 200
    assert federated.json()["member"]["email"] == "nora.diallo@example.org"
    assert federated.json()["total_hours"] == 6.5

    overview = client.get("/api/v1/federated/overview", headers=auth_headers).json()
    assert overview["member_count"] == 1
    assert overview["participant_count"] == 1
    assert overview["total_hours"] == 6.5


def test_unknown_member_and_duplicate_email(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _member(client, auth_headers)
    assert client.post(
        "/api/v1/members",
        headers=auth_headers,
        json={
            "full_name": "Nora Bis",
            "email": "nora.diallo@example.org",
            "postal_code": "35000",
            "consent": True,
        },
    ).status_code == 409
    unknown_id = str(uuid4())
    assert client.post(
        "/api/v1/participations",
        headers=auth_headers,
        json={"member_ref": unknown_id, "program": "Maraude", "hours": 1},
    ).status_code == 404
    assert client.get(
        f"/api/v1/federated/members/{unknown_id}", headers=auth_headers
    ).status_code == 404
    assert client.post(
        "/api/v1/participations",
        headers=auth_headers,
        json={"member_ref": "not-a-uuid", "program": "Maraude", "hours": 1},
    ).status_code == 422


def test_routing_policy(client: TestClient, auth_headers: dict[str, str]) -> None:
    policy = client.get("/api/v1/routing-policy", headers=auth_headers).json()
    assert "email" in policy["private"]
    assert "program" in policy["cloud"]
    assert policy["cross_database_foreign_keys"] is False

    deployment = client.get("/api/v1/deployment-info", headers=auth_headers).json()
    assert deployment == {
        "mode": "local",
        "private_database": "local",
        "cloud_database": "local",
        "cloud_tls": False,
    }


def test_members_are_paginated(client: TestClient, auth_headers: dict[str, str]) -> None:
    first = _member(client, auth_headers)
    second = _member(client, auth_headers, "ines.bernard@example.org")

    page = client.get(
        "/api/v1/members?limit=1&offset=1", headers=auth_headers
    )
    assert page.status_code == 200
    assert page.json() == [second]
    assert page.json() != [first]
    assert client.get("/api/v1/members?limit=101", headers=auth_headers).status_code == 422


def test_seed_is_idempotent(tmp_path) -> None:
    settings = Settings(
        jwt_secret="seed-secret-that-is-long-enough-for-tests",
        admin_username="tester",
        admin_password="test-password",
        private_database_url=f"sqlite:///{tmp_path / 'seed-private.sqlite3'}",
        cloud_database_url=f"sqlite:///{tmp_path / 'seed-cloud.sqlite3'}",
        auto_create_schema=True,
        seed_demo_data=True,
    )

    with TestClient(create_app(settings)):
        pass
    with TestClient(create_app(settings)) as seeded_client:
        token = seeded_client.post(
            "/api/v1/auth/token", data={"username": "tester", "password": "test-password"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert len(seeded_client.get("/api/v1/members", headers=headers).json()) == 1
        overview = seeded_client.get("/api/v1/federated/overview", headers=headers).json()
        assert overview["member_count"] == 1
        assert overview["total_hours"] == 5.5
