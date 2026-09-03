from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.domain.errors import (
    AlreadyExistsError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from src.shared.infrastructure.http.error_handlers import register_error_handlers


def _client_for(error: Exception) -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/resource")
    async def raise_error() -> None:
        raise error

    return TestClient(app, raise_server_exceptions=False)


def test_not_found_error_uses_problem_json() -> None:
    response = _client_for(NotFoundError("User no encontrado")).get("/resource")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"].endswith("/not-found")


def test_already_exists_error_uses_conflict() -> None:
    response = _client_for(AlreadyExistsError("Email ya existe")).get("/resource")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email ya existe"


def test_domain_validation_error_uses_bad_request() -> None:
    response = _client_for(DomainValidationError("Nombre inválido")).get("/resource")

    assert response.status_code == 400
    assert response.json()["type"].endswith("/validation")


def test_permission_denied_hides_domain_detail() -> None:
    response = _client_for(PermissionDeniedError("Internal policy detail")).get(
        "/resource"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permiso para realizar esta operación."
