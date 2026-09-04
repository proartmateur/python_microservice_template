from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository


class ListProducts:
    """Lista una colección acotada del agregado Product."""

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int) -> list[ProductEntity]:
        return await self._repository.list(limit=limit)
