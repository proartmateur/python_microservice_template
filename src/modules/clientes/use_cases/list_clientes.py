from src.modules.clientes.domain.entities import ClienteEntity
from src.modules.clientes.domain.repositories import ClienteRepository


class ListClientes:
    """Lista una colección acotada del agregado Cliente."""

    def __init__(self, repository: ClienteRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int) -> list[ClienteEntity]:
        return await self._repository.list(limit=limit)
