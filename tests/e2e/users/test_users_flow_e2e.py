from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.e2e


def _build_user_payload(prefix: str) -> dict[str, str]:
    token = uuid4().hex[:10]
    return {
        "nombre": f"{prefix}_{token}",
        "email": f"{prefix}.{token}@e2e.local",
    }


def _create_user(client: TestClient, prefix: str) -> dict:
    payload = _build_user_payload(prefix)
    response = client.post("/api/v1/users/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_users_full_flow_create_list_get_update_delete(client: TestClient) -> None:
    create_payload = _build_user_payload("create")

    create_response = client.post("/api/v1/users/", json=create_payload)
    assert create_response.status_code == 201, create_response.text

    created_user = create_response.json()
    user_id = created_user["id"]
    assert created_user["nombre"] == create_payload["nombre"]
    assert created_user["email"] == create_payload["email"]
    assert created_user["created_at"]

    list_response = client.get("/api/v1/users/", params={"limit": 100, "page": 0})
    assert list_response.status_code == 200, list_response.text

    list_body = list_response.json()
    assert list_body["page"] == 0
    assert list_body["limit"] == 100
    assert isinstance(list_body["total_users"], int)
    assert isinstance(list_body["total_pages"], int)
    assert isinstance(list_body["has_next"], bool)
    assert isinstance(list_body["has_prev"], bool)
    assert isinstance(list_body["items"], list)
    assert any(item["id"] == user_id for item in list_body["items"])

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["id"] == user_id

    update_payload = _build_user_payload("update")
    update_response = client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert update_response.status_code == 200, update_response.text

    updated_user = update_response.json()
    assert updated_user["id"] == user_id
    assert updated_user["nombre"] == update_payload["nombre"]
    assert updated_user["email"] == update_payload["email"]

    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204, delete_response.text

    get_after_delete_response = client.get(f"/api/v1/users/{user_id}")
    assert get_after_delete_response.status_code == 404, get_after_delete_response.text


def test_users_duplicate_email_returns_409(client: TestClient) -> None:
    payload = _build_user_payload("duplicate")

    first_create = client.post("/api/v1/users/", json=payload)
    assert first_create.status_code == 201, first_create.text

    second_create = client.post("/api/v1/users/", json=payload)
    assert second_create.status_code == 409, second_create.text
    assert "Ya existe" in second_create.json()["detail"]


def test_users_list_invalid_pagination_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/users/", params={"limit": 0, "page": -1})
    assert response.status_code == 422, response.text


def test_users_create_invalid_business_rules_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/users/",
        json={"nombre": "   ", "email": "correo-invalido"},
    )
    assert response.status_code == 400, response.text
    assert "nombre" in response.json()["detail"].lower()


def test_users_create_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/users/", json={"nombre": "sin_email"})
    assert response.status_code == 422, response.text


def test_users_get_not_found_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/users/{uuid4()}")
    assert response.status_code == 404, response.text


def test_users_get_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/users/no-es-uuid")
    assert response.status_code == 422, response.text


def test_users_update_not_found_returns_404(client: TestClient) -> None:
    payload = _build_user_payload("not_found_update")
    response = client.put(f"/api/v1/users/{uuid4()}", json=payload)
    assert response.status_code == 404, response.text


def test_users_update_duplicate_email_returns_409(client: TestClient) -> None:
    first_user = _create_user(client, "dup_update_a")
    second_user = _create_user(client, "dup_update_b")

    response = client.put(
        f"/api/v1/users/{second_user['id']}",
        json={"nombre": "renombrado", "email": first_user["email"]},
    )
    assert response.status_code == 409, response.text
    assert "Ya existe" in response.json()["detail"]


def test_users_update_invalid_business_rules_returns_400(client: TestClient) -> None:
    created_user = _create_user(client, "bad_update")

    response = client.put(
        f"/api/v1/users/{created_user['id']}",
        json={"nombre": "", "email": "sin-arroba"},
    )
    assert response.status_code == 400, response.text


def test_users_update_invalid_uuid_returns_422(client: TestClient) -> None:
    payload = _build_user_payload("invalid_uuid_update")
    response = client.put("/api/v1/users/no-es-uuid", json=payload)
    assert response.status_code == 422, response.text


def test_users_delete_not_found_returns_404(client: TestClient) -> None:
    response = client.delete(f"/api/v1/users/{uuid4()}")
    assert response.status_code == 404, response.text


def test_users_delete_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.delete("/api/v1/users/no-es-uuid")
    assert response.status_code == 422, response.text


