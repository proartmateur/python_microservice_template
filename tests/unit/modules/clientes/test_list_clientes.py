import pytest

from src.modules.clientes.domain.entities import ClienteEntity
from src.modules.clientes.use_cases.list_clientes import ListClientes


class FakeClienteRepository:
    async def list(self, *, limit: int) -> list[ClienteEntity]:
        return []


@pytest.mark.asyncio
async def test_list_clientes_respects_the_requested_limit() -> None:
    use_case = ListClientes(FakeClienteRepository())

    assert await use_case.execute(limit=10) == []
