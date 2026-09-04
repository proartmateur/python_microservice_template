import pytest

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.use_cases.list_products import ListProducts


class FakeProductRepository:
    async def list(self, *, limit: int) -> list[ProductEntity]:
        return []


@pytest.mark.asyncio
async def test_list_products_respects_the_requested_limit() -> None:
    use_case = ListProducts(FakeProductRepository())

    assert await use_case.execute(limit=10) == []
