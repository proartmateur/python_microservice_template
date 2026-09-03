from dataclasses import dataclass

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository
from src.shared.domain.find_by import FindByCriteria
from src.shared.domain.pagination import CursorCodec


@dataclass(frozen=True)
class FindByProductsResult:
    items: list[ProductEntity]
    next_cursor: str | None
    has_next: bool


class FindByProducts:
    """Busca entidades con criterios ya validados por el contrato HTTP."""

    def __init__(
        self, repository: ProductRepository, cursor_codec: CursorCodec
    ) -> None:
        self._repository = repository
        self._cursor_codec = cursor_codec

    async def execute(
        self,
        *,
        criteria: FindByCriteria,
        limit: int,
        cursor: str | None,
        pagination: bool,
    ) -> FindByProductsResult:
        position = self._cursor_codec.decode(cursor) if pagination and cursor else None
        result = await self._repository.find_by(
            criteria=criteria,
            limit=limit,
            cursor=position,
            pagination=pagination,
        )
        next_cursor = (
            self._cursor_codec.encode(result.next_position)
            if result.next_position is not None
            else None
        )
        return FindByProductsResult(
            items=result.items,
            next_cursor=next_cursor,
            has_next=result.has_next,
        )
