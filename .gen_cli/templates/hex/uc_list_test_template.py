import pytest

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.use_cases.list_<snake_name>s import List<ent>s


class Fake<ent>Repository:
    async def list(self, *, limit: int) -> list[<ent>Entity]:
        return []


@pytest.mark.asyncio
async def test_list_<snake_name>s_respects_the_requested_limit() -> None:
    use_case = List<ent>s(Fake<ent>Repository())

    assert await use_case.execute(limit=10) == []
