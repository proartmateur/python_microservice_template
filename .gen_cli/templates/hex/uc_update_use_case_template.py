from uuid import UUID

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.shared.domain.unit_of_work import UnitOfWork


class Update<ent>s:
    """Actualiza un agregado activo y confirma una unica transaccion."""

    def __init__(self, repository: <ent>Repository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        identifier: UUID,
(     $snake_prop$: $prop_type$,
)
    ) -> <ent>Entity:
        entity = await self._repository.update(
            identifier,
(     $snake_prop$=$snake_prop$,
)
        )
        await self._unit_of_work.commit()
        return entity
