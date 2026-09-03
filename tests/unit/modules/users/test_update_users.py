from uuid import uuid4

import pytest

from src.modules.users.domain.entities import UserEntity
from src.modules.users.use_cases.update_users import UpdateUsers


class FakeUserRepository:
    async def update(self, identifier: object, **values: object) -> UserEntity:
        return UserEntity(**values)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_update_users_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = UpdateUsers(FakeUserRepository(), unit_of_work)

    await use_case.execute(
        uuid4(),
    nombre=str(),
    email=str(),

    )

    assert unit_of_work.commits == 1
