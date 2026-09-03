from dataclasses import dataclass

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.shared.domain.pagination import CursorCodec


@dataclass(frozen=True)
class ListPaginated<ent>sResult:
    items: list[<ent>Entity]
    next_cursor: str | None
    has_next: bool


class ListPaginated<ent>s:
    """Lista una colección con cursor/keyset sin usar OFFSET."""

    def __init__(self, repository: <ent>Repository, cursor_codec: CursorCodec) -> None:
        self._repository = repository
        self._cursor_codec = cursor_codec

    async def execute(
        self, *, limit: int, cursor: str | None
    ) -> ListPaginated<ent>sResult:
        position = self._cursor_codec.decode(cursor) if cursor else None
        page = await self._repository.list_paginated(limit=limit, cursor=position)
        next_cursor = (
            self._cursor_codec.encode(page.next_position)
            if page.next_position is not None
            else None
        )
        return ListPaginated<ent>sResult(
            items=page.items,
            next_cursor=next_cursor,
            has_next=page.has_next,
        )
