import pytest

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.use_cases.create_<snake_name>s import Create<ent>s


class Fake<ent>Repository:
    async def save(self, entity: <ent>Entity) -> <ent>Entity:
        return entity


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_<snake_name>s_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = Create<ent>s(Fake<ent>Repository(), unit_of_work)

    await use_case.execute(
(     $snake_prop$=$prop_type$(),
)
    )

    assert unit_of_work.commits == 1
