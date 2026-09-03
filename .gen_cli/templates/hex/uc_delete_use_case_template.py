from uuid import UUID

from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.shared.domain.unit_of_work import UnitOfWork


class Delete<ent>s:
    """Elimina logicamente un agregado y confirma una unica transaccion."""

    def __init__(self, repository: <ent>Repository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(self, identifier: UUID) -> None:
        await self._repository.soft_delete(identifier)
        await self._unit_of_work.commit()
