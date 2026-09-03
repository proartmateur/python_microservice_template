from uuid import uuid4

import pytest

from src.modules.users.domain.exceptions import UserNotFoundError
from src.modules.users.use_cases.get_users import GetUsers


class FakeUserRepository:
    async def find_by_id(self, identifier: object) -> None:
        return None


@pytest.mark.asyncio
async def test_get_users_raises_not_found_for_an_unknown_identifier() -> None:
    use_case = GetUsers(FakeUserRepository())

    with pytest.raises(UserNotFoundError):
        await use_case.execute(uuid4())
