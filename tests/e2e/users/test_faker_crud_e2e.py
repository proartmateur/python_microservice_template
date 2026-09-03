import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def faker_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Levanta la app en modo faker sin Postgres con store fresco."""
    monkeypatch.setenv("REPOSITORY_DATA_SOURCE", "faker")

    # Invalidar el cache de get_settings para que relea el env.
    from src.config import get_settings
    get_settings.cache_clear()

    # Resetear el store singleton de users.
    from src.modules.users.infrastructure.http.dependencies import (
        reset_faker_user_store,
    )
    reset_faker_user_store()

    from src.main import create_app
    app = create_app()

    with TestClient(app) as client:
        yield client

    reset_faker_user_store()
    get_settings.cache_clear()


def test_health_ok_in_faker_mode(faker_client: TestClient) -> None:
    response = faker_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_users_returns_seed_data(faker_client: TestClient) -> None:
    response = faker_client.get("/api/v1/users/?limit=10")
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0
    assert all("id" in u and "nombre" in u and "email" in u for u in users)


def test_create_get_update_delete_flow(faker_client: TestClient) -> None:
    # Create
    payload = {"nombre": "FakerTest", "email": "faker.test@example.com"}
    response = faker_client.post("/api/v1/users/", json=payload)
    assert response.status_code == 201
    created = response.json()
    user_id = created["id"]
    assert created["nombre"] == "FakerTest"
    assert created["email"] == "faker.test@example.com"

    # Get
    response = faker_client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id

    # Update
    update_payload = {"nombre": "Updated", "email": "updated@example.com"}
    response = faker_client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["nombre"] == "Updated"
    assert response.json()["email"] == "updated@example.com"

    # Delete
    response = faker_client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    # Get after delete -> 404
    response = faker_client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404


def test_create_duplicate_email_returns_400(faker_client: TestClient) -> None:
    payload = {"nombre": "Dup", "email": "dup@example.com"}
    faker_client.post("/api/v1/users/", json=payload)

    payload2 = {"nombre": "Dup2", "email": "dup@example.com"}
    response = faker_client.post("/api/v1/users/", json=payload2)
    assert response.status_code == 409


def test_list_paginated_has_next(faker_client: TestClient) -> None:
    response = faker_client.get("/api/v1/users/paginated?limit=3")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "next_cursor" in body
    assert "has_next" in body
    assert len(body["items"]) <= 3


def test_find_by_contains(faker_client: TestClient) -> None:
    # Crear un usuario con nombre conocido.
    faker_client.post(
        "/api/v1/users/",
        json={"nombre": "FindableName", "email": "findable@example.com"},
    )
    response = faker_client.post(
        "/api/v1/users/find-by",
        json={
            "field": "nombre",
            "query": {"operator": "contains", "value": "Findable"},
            "pagination": False,
            "limit": 10,
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert any("FindableName" in i["nombre"] for i in items)


def test_get_nonexistent_returns_404(faker_client: TestClient) -> None:
    response = faker_client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404