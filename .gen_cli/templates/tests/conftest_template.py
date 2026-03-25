import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    # Opt-in guard: evita correr e2e contra DB real por accidente.
    if os.getenv("RUN_E2E_$const_name$S") != "1":
        pytest.skip("Define RUN_E2E_$const_name$S=1 para ejecutar los e2e de <snake_name>s.")

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
