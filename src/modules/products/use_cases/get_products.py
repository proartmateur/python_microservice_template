from uuid import UUID

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.exceptions import ProductNotFoundError
from src.modules.products.domain.repositories import ProductRepository


class GetProducts:
    """Obtiene un agregado activo por su identidad."""

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(self, identifier: UUID) -> ProductEntity:
        entity = await self._repository.find_by_id(identifier)
        if entity is None:
            raise ProductNotFoundError("Product not found")
        return entity
