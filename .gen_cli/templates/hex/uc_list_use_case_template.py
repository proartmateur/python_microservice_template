from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.repositories import <ent>Repository


class List<ent>s:
    """Lista una colección acotada del agregado <ent>."""

    def __init__(self, repository: <ent>Repository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int) -> list[<ent>Entity]:
        return await self._repository.list(limit=limit)
