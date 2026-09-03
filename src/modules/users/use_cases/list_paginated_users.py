from dataclasses import dataclass

from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.repositories import UserRepository
from src.shared.domain.pagination import CursorCodec


@dataclass(frozen=True)
class ListPaginatedUsersResult:
    items: list[UserEntity]
    next_cursor: str | None
    has_next: bool


class ListPaginatedUsers:
    """Lista una colección con cursor/keyset sin usar OFFSET."""

    def __init__(self, repository: UserRepository, cursor_codec: CursorCodec) -> None:
        self._repository = repository
        self._cursor_codec = cursor_codec

    async def execute(
        self, *, limit: int, cursor: str | None
    ) -> ListPaginatedUsersResult:
        position = self._cursor_codec.decode(cursor) if cursor else None
        page = await self._repository.list_paginated(limit=limit, cursor=position)
        next_cursor = (
            self._cursor_codec.encode(page.next_position)
            if page.next_position is not None
            else None
        )
        return ListPaginatedUsersResult(
            items=page.items,
            next_cursor=next_cursor,
            has_next=page.has_next,
        )
