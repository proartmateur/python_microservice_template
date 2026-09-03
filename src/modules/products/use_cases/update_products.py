from uuid import UUID

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository
from src.shared.domain.unit_of_work import UnitOfWork

# gencli:use-case-imports


class UpdateProducts:
    """Actualiza un agregado activo y confirma una unica transaccion."""

    def __init__(self, repository: ProductRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        identifier: UUID,
    name: str,
    price: float,
    is_physical: bool,

    ) -> ProductEntity:
        entity = await self._repository.update(
            identifier,
    name=name,
    price=price,
    is_physical=is_physical,

        )
        await self._unit_of_work.commit()
        return entity
