from uuid import uuid4

import pytest

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.use_cases.update_<snake_name>s import Update<ent>s


class Fake<ent>Repository:
    async def update(self, identifier: object, **values: object) -> <ent>Entity:
        return <ent>Entity(**values)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_update_<snake_name>s_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = Update<ent>s(Fake<ent>Repository(), unit_of_work)

    await use_case.execute(
        uuid4(),
(     $snake_prop$=$prop_type$(),
)
    )

    assert unit_of_work.commits == 1
