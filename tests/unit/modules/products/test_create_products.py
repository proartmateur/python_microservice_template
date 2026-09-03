import pytest

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.use_cases.create_products import CreateProducts


class FakeProductRepository:
    async def save(self, entity: ProductEntity) -> ProductEntity:
        return entity


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_products_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = CreateProducts(FakeProductRepository(), unit_of_work)

    await use_case.execute(
    name=str(),
    price=float(),
    is_physical=bool(),

    )

    assert unit_of_work.commits == 1
