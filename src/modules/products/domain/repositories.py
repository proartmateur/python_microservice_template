from typing import Protocol

# gencli:repository-port-imports
from src.shared.domain.find_by import FindByCriteria, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor
from uuid import UUID
from src.modules.products.domain.entities import ProductEntity

class ProductRepository(Protocol):
    """Puerto de persistencia del agregado Product."""

    # gencli:repository-port-methods
    async def soft_delete(self, identifier: UUID) -> None:
        """Elimina logicamente una entidad activa sin confirmar la transaccion."""
        ...
    async def update(self, identifier: UUID, **values: object) -> ProductEntity:
        """Actualiza una entidad activa sin confirmar la transaccion."""
        ...
    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[ProductEntity]:
        """Busca entidades activas usando un criterio validado."""
        ...
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[ProductEntity]:
        """Devuelve una página keyset de entidades activas."""
        ...
    async def list(self, *, limit: int) -> list[ProductEntity]:
        """Devuelve una colección acotada de entidades activas."""
        ...
    async def find_by_id(self, identifier: UUID) -> ProductEntity | None:
        """Busca una entidad activa por su identidad."""
        ...
    async def save(self, entity: ProductEntity) -> ProductEntity:
        """Guarda una entidad sin confirmar la transaccion."""
        ...
