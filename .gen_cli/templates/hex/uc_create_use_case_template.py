from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.shared.domain.unit_of_work import UnitOfWork

# gencli:use-case-imports


class Create<ent>s:
    """Crea un agregado y confirma una unica transaccion."""

    def __init__(self, repository: <ent>Repository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        *,
(     $snake_prop$: $prop_type$,
)
    ) -> <ent>Entity:
        entity = <ent>Entity(
(     $snake_prop$=$snake_prop$,
)
        )
        saved_entity = await self._repository.save(entity)
        await self._unit_of_work.commit()
        return saved_entity
