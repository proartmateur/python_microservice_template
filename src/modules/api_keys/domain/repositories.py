from typing import Protocol
from uuid import UUID

from datetime import datetime

from src.modules.api_keys.domain.entities import ApiKeyEntity


class ApiKeyRepository(Protocol):
    """Puerto de persistencia del agregado ApiKey."""

    async def find_by_prefix(self, prefix: str) -> ApiKeyEntity | None:
        """Busca una API key activa por su prefijo (pk_a1b2c3d4)."""
        ...

    async def save(self, entity: ApiKeyEntity) -> ApiKeyEntity:
        """Guarda una nueva API key sin confirmar la transaccion."""
        ...

    async def revoke(self, identifier: UUID) -> None:
        """Marca una API key como revocada sin confirmar la transaccion."""
        ...

    async def update_hash(
        self, identifier: UUID, new_hash: str, new_prefix: str
    ) -> None:
        """Actualiza el hash y prefijo tras una rotacion."""
        ...

    async def update_last_used(
        self, identifier: UUID, at: datetime
    ) -> None:
        """Actualiza last_used_at (batched/async, no por request)."""
        ...

    async def list(self, *, limit: int) -> list[ApiKeyEntity]:
        """Devuelve una colección acotada de API keys."""
        ...

    async def find_by_id(self, identifier: UUID) -> ApiKeyEntity | None:
        """Busca una API key por su identidad."""
        ...