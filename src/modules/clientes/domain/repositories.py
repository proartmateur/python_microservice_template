from typing import Protocol

# gencli:repository-port-imports
from uuid import UUID
from src.modules.clientes.domain.entities import ClienteEntity

class ClienteRepository(Protocol):
    """Puerto de persistencia del agregado Cliente."""

    # gencli:repository-port-methods
    async def find_by_id(self, identifier: UUID) -> ClienteEntity | None:
        """Busca una entidad activa por su identidad."""
        ...
    async def list(self, *, limit: int) -> list[ClienteEntity]:
        """Devuelve una colección acotada de entidades activas."""
        ...
