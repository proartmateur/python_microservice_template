from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.repositories import UserRepository


class ListUsers:
    """Lista una colección acotada del agregado User."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int) -> list[UserEntity]:
        return await self._repository.list(limit=limit)
