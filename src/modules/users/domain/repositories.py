from typing import Protocol

# gencli:repository-port-imports
from uuid import UUID
from src.shared.domain.find_by import FindByCriteria, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor
from src.modules.users.domain.entities import UserEntity

class UserRepository(Protocol):
    """Puerto de persistencia del agregado User."""

    # gencli:repository-port-methods
    async def soft_delete(self, identifier: UUID) -> None:
        """Elimina logicamente una entidad activa sin confirmar la transaccion."""
        ...
    async def update(self, identifier: UUID, **values: object) -> UserEntity:
        """Actualiza una entidad activa sin confirmar la transaccion."""
        ...
    async def find_by_id(self, identifier: UUID) -> UserEntity | None:
        """Busca una entidad activa por su identidad."""
        ...
    async def save(self, entity: UserEntity) -> UserEntity:
        """Guarda una entidad sin confirmar la transaccion."""
        ...
    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[UserEntity]:
        """Busca entidades activas usando un criterio validado."""
        ...
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[UserEntity]:
        """Devuelve una página keyset de entidades activas."""
        ...
    async def list(self, *, limit: int) -> list[UserEntity]:
        """Devuelve una colección acotada de entidades activas."""
        ...
