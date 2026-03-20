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

