from uuid import uuid4

import pytest

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.use_cases.update_products import UpdateProducts


class FakeProductRepository:
    async def update(self, identifier: object, **values: object) -> ProductEntity:
        return ProductEntity(**values)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_update_products_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = UpdateProducts(FakeProductRepository(), unit_of_work)

    await use_case.execute(
        uuid4(),
    name=str(),
    price=float(),
    is_physical=bool(),

    )

    assert unit_of_work.commits == 1
