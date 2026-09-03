from uuid import uuid4

import pytest

from src.modules.clientes.domain.exceptions import ClienteNotFoundError
from src.modules.clientes.use_cases.get_clientes import GetClientes


class FakeClienteRepository:
    async def find_by_id(self, identifier: object) -> None:
        return None


@pytest.mark.asyncio
async def test_get_clientes_raises_not_found_for_an_unknown_identifier() -> None:
    use_case = GetClientes(FakeClienteRepository())

    with pytest.raises(ClienteNotFoundError):
        await use_case.execute(uuid4())
