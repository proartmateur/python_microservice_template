from typing import cast

import pytest

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.use_cases.find_by_<snake_name>s import FindBy<ent>s
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import KeysetCursor
from src.shared.infrastructure.http.pagination import HmacCursorCodec


class Fake<ent>FindByRepository:
    async def find_by(
        self,
        *,
        criteria: FindByCriteria,
        limit: int,
        cursor: KeysetCursor | None,
        pagination: bool,
    ) -> FindByResult[<ent>Entity]:
        assert criteria.operator is FindByOperator.EQUALS
        assert pagination is False
        return FindByResult(
            items=[cast(<ent>Entity, object())],
            next_position=None,
            has_next=False,
        )


@pytest.mark.asyncio
async def test_find_by_<snake_name>s_returns_a_bounded_result() -> None:
    use_case = FindBy<ent>s(Fake<ent>FindByRepository(), HmacCursorCodec("a" * 32))

    result = await use_case.execute(
        criteria=FindByCriteria("any-field", FindByOperator.EQUALS, "value"),
        limit=10,
        cursor=None,
        pagination=False,
    )

    assert len(result.items) == 1
    assert result.has_next is False
