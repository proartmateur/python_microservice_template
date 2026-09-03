from typing import cast

import pytest

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.use_cases.find_by_products import FindByProducts
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import KeysetCursor
from src.shared.infrastructure.http.pagination import HmacCursorCodec


class FakeProductFindByRepository:
    async def find_by(
        self,
        *,
        criteria: FindByCriteria,
        limit: int,
        cursor: KeysetCursor | None,
        pagination: bool,
    ) -> FindByResult[ProductEntity]:
        assert criteria.operator is FindByOperator.EQUALS
        assert pagination is False
        return FindByResult(
            items=[cast(ProductEntity, object())],
            next_position=None,
            has_next=False,
        )


@pytest.mark.asyncio
async def test_find_by_products_returns_a_bounded_result() -> None:
    use_case = FindByProducts(FakeProductFindByRepository(), HmacCursorCodec("a" * 32))

    result = await use_case.execute(
        criteria=FindByCriteria("any-field", FindByOperator.EQUALS, "value"),
        limit=10,
        cursor=None,
        pagination=False,
    )

    assert len(result.items) == 1
    assert result.has_next is False
