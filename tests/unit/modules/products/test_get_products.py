from uuid import uuid4

import pytest

from src.modules.products.domain.exceptions import ProductNotFoundError
from src.modules.products.use_cases.get_products import GetProducts


class FakeProductRepository:
    async def find_by_id(self, identifier: object) -> None:
        return None


@pytest.mark.asyncio
async def test_get_products_raises_not_found_for_an_unknown_identifier() -> None:
    use_case = GetProducts(FakeProductRepository())

    with pytest.raises(ProductNotFoundError):
        await use_case.execute(uuid4())
