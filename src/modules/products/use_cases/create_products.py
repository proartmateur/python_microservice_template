from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository
from src.shared.domain.unit_of_work import UnitOfWork

# gencli:use-case-imports


class CreateProducts:
    """Crea un agregado y confirma una unica transaccion."""

    def __init__(self, repository: ProductRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def execute(
        self,
        *,
    name: str,
    price: float,
    is_physical: bool,

    ) -> ProductEntity:
        entity = ProductEntity(
    name=name,
    price=price,
    is_physical=is_physical,

        )
        saved_entity = await self._repository.save(entity)
        await self._unit_of_work.commit()
        return saved_entity
