from dataclasses import dataclass

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository
from src.shared.domain.pagination import CursorCodec


@dataclass(frozen=True)
class ListPaginatedProductsResult:
    items: list[ProductEntity]
    next_cursor: str | None
    has_next: bool


class ListPaginatedProducts:
    """Lista una colección con cursor/keyset sin usar OFFSET."""

    def __init__(
        self, repository: ProductRepository, cursor_codec: CursorCodec
    ) -> None:
        self._repository = repository
        self._cursor_codec = cursor_codec

    async def execute(
        self, *, limit: int, cursor: str | None
    ) -> ListPaginatedProductsResult:
        position = self._cursor_codec.decode(cursor) if cursor else None
        page = await self._repository.list_paginated(limit=limit, cursor=position)
        next_cursor = (
            self._cursor_codec.encode(page.next_position)
            if page.next_position is not None
            else None
        )
        return ListPaginatedProductsResult(
            items=page.items,
            next_cursor=next_cursor,
            has_next=page.has_next,
        )
