from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import pytest

from src.modules.users.domain.entities import UserEntity
from src.modules.users.use_cases.list_paginated_users import (
    ListPaginatedUsers,
)
from src.shared.domain.pagination import CursorPage, KeysetCursor
from src.shared.infrastructure.http.pagination import HmacCursorCodec


class FakeUserPaginatedRepository:
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[UserEntity]:
        entity = cast(UserEntity, object())
        return CursorPage(
            items=[entity],
            next_position=KeysetCursor(datetime.now(UTC), uuid4()),
            has_next=True,
        )


@pytest.mark.asyncio
async def test_list_paginated_users_returns_an_opaque_next_cursor() -> None:
    use_case = ListPaginatedUsers(
        FakeUserPaginatedRepository(), HmacCursorCodec("a" * 32)
    )

    page = await use_case.execute(limit=10, cursor=None)

    assert len(page.items) == 1
    assert page.has_next is True
    assert page.next_cursor is not None
