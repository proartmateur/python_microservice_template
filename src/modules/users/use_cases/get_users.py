from uuid import UUID

from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.exceptions import UserNotFoundError
from src.modules.users.domain.repositories import UserRepository


class GetUsers:
    """Obtiene un agregado activo por su identidad."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, identifier: UUID) -> UserEntity:
        entity = await self._repository.find_by_id(identifier)
        if entity is None:
            raise UserNotFoundError("User not found")
        return entity
