import pytest

from src.modules.users.domain.entities import UserEntity
from src.modules.users.use_cases.create_users import CreateUsers


class FakeUserRepository:
    async def save(self, entity: UserEntity) -> UserEntity:
        return entity


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_users_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = CreateUsers(FakeUserRepository(), unit_of_work)

    await use_case.execute(
    nombre=str(),
    email=str(),

    )

    assert unit_of_work.commits == 1
