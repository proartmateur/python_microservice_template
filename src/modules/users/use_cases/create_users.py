from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.repositories import UserRepository
from src.shared.domain.unit_of_work import UnitOfWork

# gencli:use-case-imports


class CreateUsers:
    """Crea un agregado y confirma una unica transaccion."""

    def __init__(self, repository: UserRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        *,
    nombre: str,
    email: str,

    ) -> UserEntity:
        entity = UserEntity(
    nombre=nombre,
    email=email,

        )
        saved_entity = await self._repository.save(entity)
        await self._unit_of_work.commit()
        return saved_entity
