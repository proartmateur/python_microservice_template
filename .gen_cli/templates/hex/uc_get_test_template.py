from uuid import uuid4

import pytest

from src.modules.<snake_name>s.domain.exceptions import <ent>NotFoundError
from src.modules.<snake_name>s.use_cases.get_<snake_name>s import Get<ent>s


class Fake<ent>Repository:
    async def find_by_id(self, identifier: object) -> None:
        return None


@pytest.mark.asyncio
async def test_get_<snake_name>s_raises_not_found_for_an_unknown_identifier() -> None:
    use_case = Get<ent>s(Fake<ent>Repository())

    with pytest.raises(<ent>NotFoundError):
        await use_case.execute(uuid4())
