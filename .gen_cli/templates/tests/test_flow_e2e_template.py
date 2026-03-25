from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.e2e


def _build_<snake_name>_payload(prefix: str) -> dict[str, str]:
    token = uuid4().hex[:10]
    return {
(        "$camel_prop$": f"{prefix}_{token}",
)
    }


def _create_<snake_name>(client: TestClient, prefix: str) -> dict:
    payload = _build_<snake_name>_payload(prefix)
    response = client.post("/api/v1/<kebab_name>s/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_<snake_name>s_list_invalid_pagination_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/<kebab_name>s/", params={"limit": 0, "page": -1})
    assert response.status_code == 422, response.text


def test_<snake_name>s_create_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/<kebab_name>s/", json={})
    assert response.status_code == 422, response.text


def test_<snake_name>s_get_not_found_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/<kebab_name>s/{uuid4()}")
    assert response.status_code == 404, response.text


def test_<snake_name>s_get_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/<kebab_name>s/no-es-uuid")
    assert response.status_code == 422, response.text


def test_<snake_name>s_update_invalid_uuid_returns_422(client: TestClient) -> None:
    payload = _build_<snake_name>_payload("invalid_uuid_update")
    response = client.put("/api/v1/<kebab_name>s/no-es-uuid", json=payload)
    assert response.status_code == 422, response.text


def test_<snake_name>s_delete_not_found_returns_404(client: TestClient) -> None:
    response = client.delete(f"/api/v1/<kebab_name>s/{uuid4()}")
    assert response.status_code == 404, response.text


def test_<snake_name>s_delete_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.delete("/api/v1/<kebab_name>s/no-es-uuid")
    assert response.status_code == 422, response.text

