from uuid import uuid4

import pytest

from src.modules.products.use_cases.delete_products import DeleteProducts


class FakeProductRepository:
    async def soft_delete(self, identifier: object) -> None:
        return None


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_delete_products_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = DeleteProducts(FakeProductRepository(), unit_of_work)

    await use_case.execute(uuid4())

    assert unit_of_work.commits == 1
