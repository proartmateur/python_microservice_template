from uuid import UUID

from src.modules.products.domain.repositories import ProductRepository
from src.shared.domain.unit_of_work import UnitOfWork


class DeleteProducts:
    """Elimina logicamente un agregado y confirma una unica transaccion."""

    def __init__(self, repository: ProductRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(self, identifier: UUID) -> None:
        await self._repository.soft_delete(identifier)
        await self._unit_of_work.commit()
