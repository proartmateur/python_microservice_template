import pytest

from src.modules.users.domain.entities import UserEntity
from src.modules.users.use_cases.list_users import ListUsers


class FakeUserRepository:
    async def list(self, *, limit: int) -> list[UserEntity]:
        return []


@pytest.mark.asyncio
async def test_list_users_respects_the_requested_limit() -> None:
    use_case = ListUsers(FakeUserRepository())

    assert await use_case.execute(limit=10) == []
