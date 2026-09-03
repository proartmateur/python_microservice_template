from uuid import UUID

from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.repositories import UserRepository
from src.shared.domain.unit_of_work import UnitOfWork


class UpdateUsers:
    """Actualiza un agregado activo y confirma una unica transaccion."""

    def __init__(self, repository: UserRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        identifier: UUID,
    nombre: str,
    email: str,

    ) -> UserEntity:
        entity = await self._repository.update(
            identifier,
    nombre=nombre,
    email=email,

        )
        await self._unit_of_work.commit()
        return entity
