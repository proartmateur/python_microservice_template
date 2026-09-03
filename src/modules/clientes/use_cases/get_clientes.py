from uuid import UUID

from src.modules.clientes.domain.entities import ClienteEntity
from src.modules.clientes.domain.exceptions import ClienteNotFoundError
from src.modules.clientes.domain.repositories import ClienteRepository


class GetClientes:
    """Obtiene un agregado activo por su identidad."""

    def __init__(self, repository: ClienteRepository) -> None:
        self._repository = repository

    async def execute(self, identifier: UUID) -> ClienteEntity:
        entity = await self._repository.find_by_id(identifier)
        if entity is None:
            raise ClienteNotFoundError("Cliente not found")
        return entity
