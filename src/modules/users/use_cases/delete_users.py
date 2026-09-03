from uuid import UUID

from src.modules.users.domain.repositories import UserRepository
from src.shared.domain.unit_of_work import UnitOfWork


class DeleteUsers:
    """Elimina logicamente un agregado y confirma una unica transaccion."""

    def __init__(self, repository: UserRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(self, identifier: UUID) -> None:
        await self._repository.soft_delete(identifier)
        await self._unit_of_work.commit()
