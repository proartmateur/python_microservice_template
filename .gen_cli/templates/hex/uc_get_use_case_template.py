from uuid import UUID

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.exceptions import <ent>NotFoundError
from src.modules.<snake_name>s.domain.repositories import <ent>Repository


class Get<ent>s:
    """Obtiene un agregado activo por su identidad."""

    def __init__(self, repository: <ent>Repository) -> None:
        self._repository = repository

    async def execute(self, identifier: UUID) -> <ent>Entity:
        entity = await self._repository.find_by_id(identifier)
        if entity is None:
            raise <ent>NotFoundError("<ent> not found")
        return entity
